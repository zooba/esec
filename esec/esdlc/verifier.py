'''Performs analysis of a syntax tree and identifies issues and errors.
'''
from __future__ import absolute_import
import esdlc.errors as error
from esdlc.nodes import ValueNode

# ======================================================================
# Helper functions.

def _first_ref(items):
    '''Returns the token of the first reference to the items in the
    provided sequence.
    '''
    return min(min(i.tokens) for i in items if hasattr(i, 'tokens'))

def _add(dest, src):
    '''Appends the passed items to an existing entry or creates
    a new entry.
    '''
    for key, value in src.iteritems():
        if key in dest:
            if isinstance(value, list): dest[key].extend(value)
            else: dest[key].append(value)
        else:
            if isinstance(value, list): dest[key] = value
            else: dest[key] = [value]

def _diff(src1, src2):
    '''Returns a dictionary containing items from `src1` that do
    not appear in `src2`.
    '''
    return dict((key, value) for key, value in src1.iteritems() if key not in src2)

def _add_function_or_variable(dest_in, dest_out, src):
    '''Adds a variable or the variables from a function node to a pair
    of in/out dictionaries.'''
    
    if not hasattr(src, 'tag'):
        pass
    
    elif src.tag == 'variable' and src.name not in dest_out:
        if src.external:
            _add(dest_out, { src.name: src })
        else:
            _add(dest_in, { src.name: src })
    
    elif src.tag == 'function':
        if src.name == '_assign':
            variable = src.arguments['destination']
            _add(dest_out, { variable.name: variable })
            _add_function_or_variable(dest_in, dest_out, src.arguments['source'])
        else:
            for variable in src.arguments.itervalues():
                _add_function_or_variable(dest_in, dest_out, variable)
    
    elif src.tag in ('group', 'generator'):
        _add_function_or_variable(dest_in, dest_out, src.group)
    
    elif src.tag in ('fromsource', 'joinsource'):
        for variable in src.sources:
            _add_function_or_variable(dest_in, dest_out, variable)

# ======================================================================

class Verifier(object):
    '''Performs static analysis of a syntax tree.
    
    After calling `run` on an instance, the AST passed to the
    initialiser is updated.
    '''
    
    @classmethod
    def _ast_recurse(cls, ast, target):
        '''Calls `target` for each block within `ast`.'''
        errors = []
        errors.extend(target(ast, ast.init_block))
        for block in ast.blocks.itervalues():
            errors.extend(target(ast, block))
        return errors
    
    @classmethod
    def run(cls, ast):
        '''Runs the verifier over the provided syntax tree. This
        method will only run once, and is called automatically
        when required by `errors` or `warnings`.'''
        errors = []
        
        errors.extend(cls._ast_recurse(ast, cls._calculate_all_variables))
        errors.extend(cls._ast_recurse(ast, cls._resolve_implicit_parameters))
        errors.extend(cls._ast_recurse(ast, cls._calculate_variables_in_out))
        
        errors.extend(cls._ast_recurse(ast, cls._check_privates))
        errors.extend(cls._verify_namespace(ast))
        
        errors.extend(cls._calculate_globals(ast))
        errors.extend(cls._calculate_constants(ast))
        
        errors.extend(cls._calculate_filters(ast))
        
        errors.extend(cls._verify_initialiser(ast))
        
        errors.extend(cls._verify_unused(ast))
        errors.extend(cls._ast_recurse(ast, cls._verify_groups))
        
        ast._errors.extend(errors)  #pylint: disable=W0212
    
    # ==================================================================
    
    @classmethod
    def _calculate_all_variables(cls, ast, block):
        '''Produces a list of all variables created or specified
        anywhere in the system.
        '''
        
        for node in block.children:
            assert node.tag in (
                'from', 'join', 'eval', 'repeat', 'block', 'function',
                'yield', 'unknown', 'backtick', 'value', 'variable'
                ), "Unhandled tag: " + repr(node)
            
            if node.tag == 'variable':
                ast.variables.add(node.name)
            
            elif node.tag == 'function':
                if node.name == '_assign':
                    ast.variables.add(node.arguments['destination'].name)
            
            elif node.tag in ('from', 'join'):
                groups = [g.group.name for g in node.destinations if g.tag == 'group']
                ast.variables.update(groups)
            
            elif node.tag in ('block', 'repeat'):
                cls._calculate_all_variables(ast, node)
        
        return []
    
    # ==================================================================
    
    @classmethod
    def _calculate_variables_in_out(cls, ast, block):
        '''Determines which variables are required at the start of
        the block and which variables are defined at the end of the
        block.
        '''
        
        block.variables_in = variables_in = { }
        block.variables_out = variables_out = { }
        block.groups_local = groups_local = { }
        
        for node in block.children:
            assert node.tag in (
                'from', 'join', 'eval', 'repeat', 'block', 'function',
                'yield', 'unknown', 'backtick', 'value', 'variable'
                ), "Unhandled tag: " + repr(node)
            
            if node.tag == 'variable':
                # a lone variable is treated as a definition
                _add(variables_out, { node.name: node })
            
            elif node.tag == 'function':
                _add_function_or_variable(variables_in, variables_out, node)
            
            elif node.tag in ('from', 'join'):
                _add_function_or_variable(variables_in, variables_out, node.using)
                
                groups = dict((g.group.name, g.group) for g in node.destinations if g.tag == 'group')
                _add(variables_out, groups)
                _add(groups_local, _diff(groups, variables_in))
                for size in (g.size for g in node.destinations if g.tag == 'group' and g.size):
                    _add_function_or_variable(variables_in, variables_out, size)
            
            elif node.tag == 'eval':
                groups = dict((g.group.name, g.group) for g in node.sources if g.tag == 'group')
                _add(variables_in, _diff(groups, variables_out))
                
                for func_node in node.using:
                    _add_function_or_variable(variables_in, variables_out, func_node)
            
            elif node.tag in ('block', 'repeat'):
                count = getattr(node, 'count', None)
                _add_function_or_variable(variables_in, variables_out, count)
                
                cls._calculate_variables_in_out(ast, node)
                _add(variables_in, _diff(node.variables_in, variables_out))
                _add(variables_out, node.variables_out)
                _add(groups_local, node.groups_local)
        
        return []
    
    # ==================================================================
    
    @classmethod
    def _resolve_implicit_parameter(cls, variables, func_node):
        '''Replaces implicit parameters with a boolean ``True`` or
        resets the ``implicit`` flag if a matching variable exists.
        '''
        
        args = list(func_node.arguments.iterkeys())
        for arg_name in args:
            arg_value = func_node.arguments[arg_name]
            if arg_value.tag == 'variable' and arg_value.implicit:
                if arg_value.name in variables:
                    arg_value.implicit = False
                else:
                    func_node.arguments[arg_name] = ValueNode(True, arg_value.tokens)
            elif arg_value.tag == 'function':
                cls._resolve_implicit_parameter(variables, arg_value)
            elif arg_value.tag in ('fromsource', 'joinsource'):
                for src in arg_value.sources:
                    if src.tag == 'generator':
                        cls._resolve_implicit_parameter(variables, src.group)
                    elif src.tag == 'function':
                        cls._resolve_implicit_parameter(variables, src)
    
    # ==================================================================
    
    @classmethod
    def _resolve_implicit_parameters(cls, ast, block):
        '''Recursively replaces implicit parameters with a boolean
        ``True`` or resets the ``implicit`` flag if a matching variable
        exists.
        '''
        
        errors = []
        
        variables = ast.variables
        for node in block.children:
            if node.tag == 'function':
                cls._resolve_implicit_parameter(variables, node)
            elif node.tag == 'generator':
                cls._resolve_implicit_parameter(variables, node.group)
            elif node.tag in ('from', 'join'):
                if node.using.tag in ('fromsource', 'joinsource'):
                    for src in node.using.sources:
                        if src.tag == 'generator':
                            cls._resolve_implicit_parameter(variables, src.group)
                        elif src.tag == 'function':
                            cls._resolve_implicit_parameter(variables, src)
                elif node.using.tag == 'function':
                    cls._resolve_implicit_parameter(variables, node.using)
                
            elif node.tag in ('block', 'repeat'):
                errors.extend(cls._resolve_implicit_parameters(ast, node))
        
        return errors
    
    # ==================================================================
    
    @classmethod
    def _check_privates(cls, ast, block):       #pylint: disable=W0613
        '''Identify variables that may conflict with private names.'''
        
        warn_private = { }
        
        warn_private.update((key, value) for key, value in block.variables_in.iteritems() if key[0] == '_')
        warn_private.update((key, value) for key, value in block.variables_out.iteritems() if key[0] == '_')
        
        # Don't warn about externally defined
        warn_private = dict((key, value) for key, value in warn_private.iteritems()
                            if value and not (any(v.tag == 'variable' and v.external for v in value)))
        
        return [error.InternalVariableNameError(_first_ref(value), key)
                for key, value in warn_private.iteritems()]
    
    # ==================================================================
    
    @classmethod
    def _calculate_globals(cls, ast):
        '''Fill the `globals` property with groups and variables that
        must be retained between blocks.
        '''
        
        ast.globals = global_vars = dict(ast.init_block.variables_out)
        
        for block in ast.blocks.itervalues():
            global_vars.update(block.variables_in)
        
        return []
    
    @classmethod
    def _calculate_constants(cls, ast):
        '''Fill the `constants` property with groups and variables that
        never change after initialisation.
        '''
        
        ast.constants = constants = dict(ast.globals)
        
        for block in ast.blocks.itervalues():
            for var in block.variables_out:
                if var in constants: del constants[var]
        
        return []
    
    @classmethod
    def _calculate_filters(cls, ast):
        '''Determines all the filters used in the system.'''
        ast.filters = filters = list(cls._calculate_filters_recurse(ast, ast.init_block))
        for block in ast.blocks.itervalues():
            filters.extend(cls._calculate_filters_recurse(ast, block))
        
        return []
    
    @classmethod
    def _calculate_filters_recurse(cls, ast, block):
        '''Determines all the filters used in a block.'''
        for node in block.children:
            if node.tag == 'from':
                using = node.using
                while using and using.tag == 'function' and using.name != '_iter':
                    yield using.name
                    using = using.arguments.get('_source', None)
            elif node.tag in ('repeat', 'block'):
                for name in cls._calculate_filters_recurse(ast, node):
                    yield name
    
    # ==================================================================
    
    @classmethod
    def _verify_initialiser(cls, ast):
        '''Ensure that all global variables and all constants are
        initialised in the initialiser block.
        '''
        
        init_variables = dict(ast.init_block.variables_out)
        uninit_global = dict(ast.globals)
        uninit_const = dict(ast.constants)
        for k in init_variables:
            if k in uninit_global: del uninit_global[k]
            if k in uninit_const: del uninit_const[k]
        
        # Don't warn twice about globals and constants
        for k in uninit_const:
            if k in uninit_global: del uninit_global[k]
        
        uninit_other = dict(ast.init_block.variables_in)
        for k in uninit_global:
            if k in uninit_other: del uninit_other[k]
        for k in uninit_const:
            if k in uninit_other: del uninit_other[k]
        
        errors = []
        errors.extend(error.UninitialisedGlobalError(_first_ref(var), key)
                      for key, var in uninit_global.iteritems())
        errors.extend(error.UninitialisedConstantError(_first_ref(var), key)
                      for key, var in uninit_const.iteritems())
        errors.extend(error.UninitialisedVariableError(_first_ref(var), key)
                      for key, var in uninit_other.iteritems())
        
        uninit = []
        uninit.extend(k for k in uninit_global.iterkeys())
        uninit.extend(k for k in uninit_const.iterkeys())
        uninit.extend(k for k in uninit_other.iterkeys())
        
        for i in xrange(len(uninit)):
            if '.' in uninit[i]:
                uninit[i] = uninit[i][:uninit[i].index('.')]
        ast.uninitialised = uninit
        
        return errors
    
    # ==================================================================
    
    @classmethod
    def _verify_unused(cls, ast):
        '''Ensure that all global variables and groups are used.'''
        
        unused_global = dict(i for i in ast.globals.iteritems()
                               if i[0] not in ast.init_block.variables_in and
                                  i[0] not in ast.init_block.variables_out)
        
        for block in ast.blocks.itervalues():
            unused_global = dict(i for i in unused_global.iteritems()
                                   if i[0] not in block.variables_in and
                                      i[0] not in block.variables_out)
        
        return [error.UnusedVariableError(_first_ref(var), key)
                for key, var in unused_global.iteritems()]
    
    # ==================================================================
    
    @classmethod
    def _verify_namespace(cls, ast):
        '''Identify naming collisions between blocks and all variables
        (and groups).
        '''
        
        error_ambiguous = set()
        
        for var in ast.init_block.variables_out:
            if var in ast.blocks: error_ambiguous.add(var)
        
        for block in ast.blocks.itervalues():
            for var in block.variables_out:
                if var in ast.blocks: error_ambiguous.add(var)
        
        return [error.AmbiguousVariableBlockNameError(min(ast.blocks[name].tokens), name)
                for name in error_ambiguous]
    
    # ==================================================================
    
    @classmethod
    def _verify_groups(cls, ast, block):
        '''Ensure groups are specified correctly, including size
        specifications.
        '''
        
        errors = []
        
        for node in block.children:
            if node.tag in ('from', 'join'):
                dests = node.destinations
                
                # Detect groups appearing more than once
                distinct_dests = set(dest.group.name for dest in dests)
                if len(distinct_dests) < len(dests):
                    duplicate_dests = []
                    for dest in dests:
                        if dest.group.name in distinct_dests:
                            distinct_dests.remove(dest.group.name)
                        else:
                            duplicate_dests.append(dest)
                    errors.extend(error.RepeatedDestinationGroupError(min(dest.tokens), dest.group.name)
                                  for dest in duplicate_dests)
                
                # Detect groups appearing after an unbounded group
                all_bounded = True
                for dest in dests:
                    if all_bounded:
                        if dest.size is None: all_bounded = False
                    else:
                        errors.append(error.UnusedGroupError(min(dest.tokens), dest.group.name))
                
                # Detect group sizes specified as a list
                errors.extend(error.InvalidGroupSizeError(min(dest.tokens), dest.group.name)
                              for dest in dests
                              if dest.size and dest.size.tag == 'function' and dest.size.name == '_list')
                
                sources = node.sources
                
                # Detect sizes specified on source groups
                errors.extend(error.UnexpectedGroupSizeError(min(src.tokens), src.group.name)
                              for src in sources
                              if getattr(src, 'size', None))
            
            elif node.tag in ('block', 'repeat'):
                errors.extend(cls._verify_groups(ast, node))
        
        return errors
