'''Constructs code executable by ``esec`` from an ESDL syntax tree.
'''
# Disable: Method could be a function
#          Too many public methods
#pylint: disable=R0201,R0904

from __future__ import absolute_import
import sys

class EsecEmitter(object):
    '''Constructs code executable by ``esec`` from an ESDL syntax tree.
    '''
    INDENT = '    '
    
    UNSAFE_VARIABLES = ['lambda']
    UNSAFE_VARIABLE_INIT = ['_%s = globals().get("%s", None)' % (i, i) for i in UNSAFE_VARIABLES]
    
    if sys.version_info.major == 3:
        RANGE_COMMAND = 'range'
    else:
        RANGE_COMMAND = 'xrange'
        
    
    FUNCTIONS = {
        '_assign': '%(destination)s = %(source)s',
        #'_call': handled separately
        #'_list': handled separately
        '_getattr': '%(source)s.%(attr)s',
        '_getitem': '%(source)s[int(%(key)s) if isinstance(%(source)s, (list, tuple)) else %(key)s]',
        '_getitem_int': '%(source)s[%(key)s]',
        '_op_+': '(%(#0)s + %(#1)s)',
        '_op_-': '(%(#0)s - %(#1)s)',
        '_op_*': '(%(#0)s * %(#1)s)',
        '_op_/': '(%(#0)s / %(#1)s)',
        '_op_//': '(%(#0)s // %(#1)s)',
        '_op_%': '(%(#0)s %% %(#1)s)',
        '_op_^': '(%(#0)s ** %(#1)s)',
        '_op_<<': '(%(#0)s << %(#1)s)',
        '_op_>>': '(%(#0)s >> %(#1)s)',
        '_uop_-': '(-%(#0)s)',
    }
    
    def write_function(self, node):
        '''Emits code for function nodes.'''
        fmt = self.FUNCTIONS.get(node.name, None)
        args = dict((k, ''.join(self.write(v))) for k, v in node.arguments.iteritems())
        if node.name == '_getitem':
            if node.arguments['key'].tag == 'value':
                yield (self.FUNCTIONS['_getitem_int'] %
                       { 'source': args['source'], 'key': str(int(node.arguments['key'].value)) })
            else:
                yield fmt % args
        elif fmt:
            yield fmt % args
        else:
            func_name = node.name
            if func_name == '_call':
                func_name = args['_target']
                del args['_target']
            
            if 'lambda' in args:
                args['lambda_'] = args['lambda']
                del args['lambda']
            allargs = sorted(args.iteritems(), key=lambda i: i[0])
            arglist = ', '.join([value for key, value in allargs if key[0] == '#'] +
                                ['%s=%s' % (key, value) for key, value in allargs if key[0] != '#'])
            
            if node.name == '_list':
                yield '[' + arglist + ']'
            else:
                yield func_name + '(' + arglist + ')'
    
    def write_name(self, node):
        '''Emits text for named nodes.'''
        yield node.name
    
    def write_text(self, node):
        '''Emits text for text nodes.'''
        yield node.text
    
    def write_value(self, node):
        '''Emits text for value nodes.'''
        return (str(node.value),)
    
    @classmethod
    def safe_variable(cls, name):
        '''Ensures variable names are valid Python.'''
        assert '[' not in name and ']' not in name, "No indexers allowed in variables"
        assert '(' not in name and ')' not in name, "No parentheses allowed in variables"
        if name in cls.UNSAFE_VARIABLES:
            name = '_' + name
        return name
    
    @classmethod
    def safe_argument(cls, name):
        '''Ensures variable names are valid as arguments.'''
        if name in cls.UNSAFE_VARIABLES:
            name = '_' + name
        return name
    
    def write_variable(self, node):
        '''Emits text for variable nodes.'''
        if node.implicit:
            yield 'globals().get("%s", True)' % self.safe_variable(node.name)
        else:
            yield self.safe_variable(node.name)
    
    def write_unknown(self, node):
        '''Emits text for unknown nodes.'''
        return self.write_text(node)
    
    def write_backtick(self, node):
        '''Emits text for backtick nodes.'''
        return self.write_text(node)
    
    def write_group(self, node):
        '''Emits text for group nodes.'''
        yield node.group.name
    
    def write_generator(self, node):
        '''Emits code for group generators.'''
        return self.write_function(node.group)
    
    def write_from(self, node):
        '''Emits code for FROM-SELECT statements.'''
        yield '# ' + str(node)
        
        # using includes the source groups
        src = ''.join(self.write(node.using))
        if all(d.size for d in node.destinations):
            src = '(_.born() for _ in ' + src + ')'
        else:
            src = '_born_iter(' + src + ')'
        
        if len(node.destinations) > 1 or node.destinations[0].size:
            yield '_gen = ' + src
            src = '_gen'
        
        for group in node.destinations:
            group_name = ''.join(self.write(group.group))
            if group.size:
                group_size = ''.join(self.write(group.size))
                i = None
                try:
                    i = int(float(group_size))
                except ValueError:
                    i = None
                
                if i is None:
                    yield '%s[:] = _islice(_gen, int(%s))' % (group_name, group_size)
                elif i == 0:
                    yield '%s[:] = []' % group_name
                elif i == 1:
                    yield '%s[:] = _islice(_gen, 1)' % group_name
                else:
                    yield '%s[:] = _islice(_gen, %d)' % (group_name, i)
            else:
                yield '%s[:] = %s.rest()' % (group_name, src)
                break
    
    def write_fromsource(self, node):
        '''Emits code for source groups in FROM-SELECT statements.'''
        sources = [''.join(self.write(s)) for s in node.sources]
        yield '_iter(' + ', '.join(sources) + ')'
    
    def write_join(self, node):
        '''Emits code for JOIN-INTO statements.'''
        yield '# ' + str(node)
        
        # using includes the source groups
        src = ''.join(self.write(node.using))
        if node.using.tag == 'joinsource':
            src = '_default_joiner(' + src + ')'
        if all(d.size for d in node.destinations):
            src = '(_.born() for _ in ' + src + ')'
        else:
            src = '_born_iter(' + src + ')'
        yield '_gen = ' + src
        
        for group in node.destinations:
            group_name = ''.join(self.write(group.group))
            if group.size:
                group_size = ''.join(self.write(group.size))
                yield '%s[:] = _islice(_gen, int(%s))' % (group_name, group_size)
            else:
                yield '%s[:] = _gen.rest()' % group_name
                break
    
    def write_joinsource(self, node):
        '''Emits code for source groups in JOIN-INTO statements.'''
        sources = [''.join(self.write(s)) for s in node.sources]
        yield ('([' + ', '.join(sources) + '], ' +
               '[' + ', '.join('"%s"' % s for s in sources) + '])')
    
    def write_eval(self, node):
        '''Emits code for EVAL statements.'''
        yield '# ' + str(node)
        
        if node.using:
            gen = node.using[0]
            if gen.tag == 'function':
                yield '_eval = ' + ''.join(self.write(gen))
            elif gen.tag == 'variable':
                name = gen.name
                yield '_eval = %s() if isinstance(%s, type) else %s' % (name, name, name)
        else:
            yield '_eval = None'
        
        yield 'for _indiv in _iter(' + ', '.join(''.join(self.write(s)) for s in node.sources) + '):'
        yield self.INDENT + '_indiv._eval = _eval'
        yield self.INDENT + 'del _indiv.fitness'
    
    def write_yield(self, node):
        '''Emits codes for YIELD statements.'''
        yield '# ' + str(node)
        for source in node.sources:
            source_name = ''.join(self.write(source))
            yield '_on_yield("%s", %s)' % (source_name, source_name)
    
    def write_block(self, node):
        '''Emits code for an entire named block.'''
        parameters = sorted(self.safe_argument(n) for n in node.variables_in.iterkeys())
        
        vars_out = [key for key, value in node.variables_out.iteritems() 
                    if not all(v.tag == 'variable' and v.external for v in value)]
        returned = sorted(self.safe_argument(n) for n in set(vars_out) & set(self.ast.globals.iterkeys()))
        global_vars = sorted(self.safe_variable(n) for n in returned) # variable is stricter than argument
        arguments = ['_copy(' + n + ')' if n in global_vars else n for n in parameters]
        
        parameters = ', '.join(parameters)
        returned = ', '.join(returned)
        global_vars = ', '.join(global_vars)
        arguments = ', '.join(arguments)
        
        yield 'def __block_%s(%s):' % (node.name, parameters)
        
        local_groups = list(node.groups_local.iterkeys())
        if local_groups:
            yield self.INDENT + ', '.join(local_groups) + ' = ' + ', '.join('[]' for _ in local_groups)
        
        for child in node.children:
            if child.tag in ('variable', 'comment'):
                continue
            
            for line in self.write(child):
                yield self.INDENT + line
        yield self.INDENT + 'return ' + returned
        yield ''
        
        yield 'def _block_' + node.name + '():'
        if returned and global_vars:
            yield self.INDENT + 'global ' + global_vars
            yield self.INDENT + '%s = __block_%s(%s)' % (returned, node.name, arguments)
        else:
            yield self.INDENT + '__block_%s(%s)' % (node.name, arguments)
        yield ''
    
    def write_repeat(self, node):
        '''Emits code for a REPEAT block.'''
        if node.children:
            count = ''.join(self.write(node.count))
            yield 'for _ in %s(int(%s)):' % (self.RANGE_COMMAND, count)
            for child in node.children:
                for line in self.write(child):
                    yield self.INDENT + line
            yield ''
    
    def write(self, node):
        '''Selects the correct overload depending on the type of `node`.
        '''
        return getattr(self, 'write_' + node.tag)(node)
    
    def emit_to_list(self):
        '''Emits the entire system to a list. Each element of the list
        is one line of code. The entire block of Python code can be
        obtained using ``'\n'.join(emitter.emit_to_list())``.
        '''
        result = []
        ast = self.ast
        
        # prepare unsafe variables
        result.extend(self.UNSAFE_VARIABLE_INIT)
        result.append('')
        
        # write initialisation block
        result.extend(self.write(ast.init_block))
        
        # write other blocks
        for block in sorted(ast.blocks.itervalues(), key=lambda b: b.index):
            result.extend(self.write(block))
        
        # call initialisation block
        result.append('_block_' + ast.init_block.name + '()')
        result.append('')
        
        # done
        return result
    
    def emit(self, out):
        '''Emits the entire system to a file-like object. `out` must
        provide a ``write`` method.
        '''
        for line in self.emit_to_list():
            out.write(line)
            out.write('\n')
    
    def __init__(self, ast):
        '''Initialises an emitter for the provided syntax tree. If
        `ast` evaluates to ``False`` or ``ast.errors`` evaluates to
        ``True``, a ``ValueError`` is raised.
        '''
        if not ast: raise ValueError("A syntax tree must be provided.")
        if ast.errors: raise ValueError("Cannot emit a syntax tree with errors.")
        self.ast = ast
