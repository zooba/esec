'''Performs analysis of a syntax tree and identifies issues and errors.
'''
from __future__ import absolute_import
import esdlc.errors as error

from esdlc.nodes import _add, _diff
def _add_function_or_variable(dest_in, dest_out, src):
    '''Adds a variable or the variables from a function node to a pair
    of in/out dictionaries.'''
    
    if not hasattr(src, 'tag') or src.tag not in ('variable', 'function'):
        pass
    elif src.tag == 'variable' and src.name not in dest_out:
        _add(dest_in, { src.name: src })
    elif src.tag == 'function':
        _add(dest_in, _diff(src.variables_in, dest_out))
        _add(dest_out, src.variables_out)

class Verifier(object):
    '''Performs static analysis of a syntax tree.
    
    After calling `run` on an instance, the AST passed to the
    initialiser is updated.
    '''
    
    @classmethod
    def _ast_recurse(cls, ast, target):
        '''Calls `target` for each block within `ast`.'''
        errors = []
        errors.extend(target(ast.init_block))
        for block in ast.blocks.itervalues():
            errors.extend(target(block))
        return errors
    
    @classmethod
    def run(cls, ast):
        '''Runs the verifier over the provided syntax tree. This
        method will only run once, and is called automatically
        when required by `errors` or `warnings`.'''
        errors = []
        
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
    
    @classmethod
    def _first_ref(cls, items):
        '''Returns the token of the first reference to the items in the
        provided sequence.
        '''
        return min(min(i.tokens) for i in items if hasattr(i, 'tokens'))
    
    @classmethod
    def _calculate_variables_in_out(cls, block=None):
        '''Determines which variables are required at the start of
        the block and which variables are defined at the end of the
        block.'''
        
        block.variables_in = variables_in = { }
        block.variables_out = variables_out = { }
        block.groups_local = groups_local = { }
        for node in block.children:
            assert node.tag in (
                'from', 'join', 'eval', 'repeat', 'block', 'function',
                'yield', 'unknown', 'backtick', 'value', 'variable'
                ), "Unhandled tag: " + repr(node)
            
            if node.tag == 'function':
                _add(variables_in, _diff(node.variables_in, variables_out))
                _add(variables_out, node.variables_out)
            
            elif node.tag in ('from', 'join'):
                if node.using.tag in ('fromsource', 'joinsource'):
                    for group in node.using.sources:
                        _add_function_or_variable(variables_in, variables_out, group.group)
                else:
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
                
                cls._calculate_variables_in_out(node)
                _add(variables_in, _diff(node.variables_in, variables_out))
                _add(variables_out, node.variables_out)
                _add(groups_local, node.groups_local)
        
        return []
    
    @classmethod
    def _check_privates(cls, block):
        '''Identify variables that may conflict with private names.'''
        
        warn_private = { }
        
        warn_private.update((key, value) for key, value in block.variables_in.iteritems() if key[0] == '_')
        warn_private.update((key, value) for key, value in block.variables_out.iteritems() if key[0] == '_')
        
        return [error.InternalVariableNameError(cls._first_ref(value), key)
                for key, value in warn_private.iteritems()]
    
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
        ast.filters = filters = list(cls._calculate_filters_recurse(ast.init_block))
        for block in ast.blocks.itervalues():
            filters.extend(cls._calculate_filters_recurse(block))
        
        return []
    
    @classmethod
    def _calculate_filters_recurse(cls, block):
        '''Determines all the filters used in a block.'''
        for node in block.children:
            if node.tag == 'from':
                using = node.using
                while using and using.tag == 'function' and using.name != '_iter':
                    yield using.name
                    using = using.arguments.get('_source', None)
            elif node.tag in ('repeat', 'block'):
                for name in cls._calculate_filters_recurse(node):
                    yield name
    
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
        
        ast.external_variables = set(uninit_other.iterkeys())
        
        errors = []
        errors.extend(error.UninitialisedGlobalError(cls._first_ref(var), key)
                      for key, var in uninit_global.iteritems())
        errors.extend(error.UninitialisedConstantError(cls._first_ref(var), key)
                      for key, var in uninit_const.iteritems())
        errors.extend(error.UninitialisedVariableError(cls._first_ref(var), key)
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
        
        return [error.UnusedVariableError(cls._first_ref(var), key)
                for key, var in unused_global.iteritems()]
    
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
    
    @classmethod
    def _verify_groups(cls, block):
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
                errors.extend(cls._verify_groups(node))
        
        return errors
