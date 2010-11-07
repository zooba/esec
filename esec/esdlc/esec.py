from __future__ import absolute_import
import sys

class EsecEmitter(object):
    INDENT = '    '
    
    DEFINITIONS = '''from itertools import islice

def _iter(*srcs):
    for src in srcs:
        for indiv in (getattr(src, '__iter__', None) or getattr(src, '__call__'))():
            yield indiv

class _born_iter(object):
    def __init__(self, src): self.src = iter(src)
    def rest(self): return [i.born() for i in getattr(self.src, 'rest', self.src.__iter__)()]
    def __iter__(self): return self
    def next(self): return next(self.src).born()'''
    '''Definitions used in compiled systems.

    The ``_iter`` method automatically calls ``__iter__`` or ``__call__`` depending
    on the parameter type, allowing constructors and lists to be used interchangeably.
    If multiple sequences are provided they are concatenated as required by
    ``FROM-SELECT`` statements.

    The ``_born_iter`` class calls the ``born`` method of individuals after a
    ``FROM-SELECT`` statement and handles calls to ``rest`` when the underlying
    sequence does not support it.
    '''
    
    FUNCTIONS = {
        '_assign': '%(destination)s = %(source)s',
        #'_call': handled separately
        #'_list': handled separately
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
        fmt = self.FUNCTIONS.get(node.name, None)
        args = dict((k, ''.join(self.write(v))) for k, v in node.arguments.iteritems())
        if node.name == '_getitem':
            if node.arguments['key'].tag == 'value':
                yield self.FUNCTIONS['_getitem_int'] % \
                    { 'source': args['source'], 'key': str(int(node.arguments['key'].value)) }
            else:
                yield fmt % args
        elif fmt:
            yield fmt % args
        else:
            func_name = node.name
            if func_name == '_call':
                func_name = args['_source']
                del args['_source']
            
            allargs = sorted(args.iteritems(), key=lambda i: i[0])
            arglist = ', '.join([value for key, value in allargs if key[0] == '#'] + \
                                ['%s=%s' % item for item in allargs if key[0] != '#'])
            
            if node.name == '_list':
                yield '[' + arglist + ']'
            else:
                yield func_name + '(' + arglist + ')'
    
    def write_name(self, node):
        yield node.name
    
    def write_text(self, node):
        yield node.text
    
    def write_value(self, node):
        return (str(node.value),)
    
    @classmethod
    def safe_variable(cls, name, replace_dots=True):
        if replace_dots and '.' in name:
            name = '_dotted_' + name.replace('.', '_')
        assert '[' not in name and ']' not in name, "No indexers allowed in variables"
        assert '(' not in name and ')' not in name, "No parentheses allowed in variables"
        if name == 'lambda': name = '_lambda'
        return name
    
    @classmethod
    def safe_argument(cls, name):
        if name == 'lambda': name = 'globals()["lambda"]'
        return name
    
    @classmethod
    def base_variable(cls, name):
        if '.' in name:
            name = name[:name.index('.')]
        assert '[' not in name and ']' not in name, "No indexers allowed in variables"
        assert '(' not in name and ')' not in name, "No parentheses allowed in variables"
        return name
    
    def write_variable(self, node):
        yield self.safe_variable(node.name)
    
    def write_unknown(self, node): return self.write_text(node)
    def write_backtick(self, node): return self.write_text(node)
    def write_filter(self, node): return self.write_function(node)
    def write_evaluator(self, node): return self.write_function(node)
    
    def write_group(self, node):
        yield node.group.name
    
    def write_generator(self, node):
        return self.write_function(node.group)
    
    def write_from(self, node):
        yield '# ' + str(node)
        
        # using includes the source groups
        src = '_born_iter(' + ''.join(self.write(node.using)) + ')'
        if len(node.destinations) > 1 or node.destinations[0].size:
            yield '_gen = ' + src
            src = '_gen'
        
        for g in node.destinations:
            group_name = ''.join(self.write(g.group))
            if g.size:
                group_size = ''.join(self.write(g.size))
                yield '%s[:] = islice(_gen, int(%s))' % (group_name, group_size)
            else:
                yield '%s[:] = %s.rest()' % (group_name, src)
                break
    
    def write_join(self, node):
        yield '# ' + str(node)
        
        # using includes the source groups
        if node.using.tag == 'joinsource':
            yield '_gen = _born_iter(_default_joiner(' + ''.join(self.write(node.using)) + '))'
        else:
            yield '_gen = _born_iter(' + ''.join(self.write(node.using)) + ')'
        
        for g in node.destinations:
            group_name = ''.join(self.write(g.group))
            if g.size:
                group_size = ''.join(self.write(g.size))
                yield '%s[:] = islice(_gen, int(%s))' % (group_name, group_size)
            else:
                yield '%s[:] = _gen.rest()' % group_name
                break
    
    def write_joinsource(self, node):
        sources = [''.join(self.write(s)) for s in node.sources]
        yield '([' + ', '.join(sources) + '], ' + \
               '[' + ', '.join('"%s"' % s for s in sources) + '])'
    
    def write_eval(self, node):
        yield '# ' + str(node)
        
        if node.using:
            gen = node.using[0]
            if gen.arguments:
                yield '_eval = ' + ''.join(self.write(gen))
            else:
                name = gen.name
                yield '_eval = %s() if isinstance(%s, type) else %s' % (name, name, name)
        else:
            yield '_eval = None'
        
        yield 'for _indiv in _iter(' + ', '.join(''.join(self.write(s)) for s in node.sources) + '):'
        yield '    _indiv._eval = _eval'
        yield '    del _indiv.fitness'
    
    def write_yield(self, node):
        yield '# ' + str(node)
        for s in node.sources:
            source_name = ''.join(self.write(s))
            yield '_on_yield("%s", %s)' % (source_name, source_name)
    
    def write_block(self, node):
        variables_in = ', '.join(sorted(self.safe_argument(n) for n in node.variables_in))
        variables_in_safe = ', '.join(sorted(self.safe_variable(n) for n in node.variables_in))
        variables_out = ', '.join(sorted(set(node.variables_out).intersection(self.ast.globals)))
        variables_out_safe = ', '.join(sorted(self.safe_variable(n) for n in set(node.variables_out).intersection(self.ast.globals)))
        variables_out_base = ', '.join(sorted(self.base_variable(n) for n in set(node.variables_out).intersection(self.ast.globals)))
        yield 'def __block_%s(%s):' % (node.name, variables_in_safe)
        local_groups = list(node.groups_local.iterkeys())
        if local_groups:
            yield '    ' + ', '.join(local_groups) + ' = ' + ', '.join('[]' for _ in local_groups)
        
        for child in node.children:
            for line in self.write(child):
                yield '    ' + line
        yield '    return ' + variables_out
        yield ''
        
        yield 'def _block_' + node.name + '():'
        if variables_out and variables_out_base:
            yield '    global ' + variables_out_base
            yield '    %s = __block_%s(%s)' % (variables_out, node.name, variables_in)
        else:
            yield '    __block_%s(%s)' % (node.name, variables_in)
        yield ''
    
    def write_repeat(self, node):
        if node.children:
            count = ''.join(self.write(node.count))
            yield 'for _ in xrange(' + count + '):'
            for c in node.children:
                for el in self.write(c):
                    yield '    ' + el
            yield ''
    
    def write(self, node):
        return getattr(self, 'write_' + node.tag)(node)
    
    def emit_to_list(self):
        result = []
        ast = self.ast
        
        # write global definitions
        result.extend(self.DEFINITIONS.splitlines())
        result.append('')
        
        # 'declare' global groups and variables
        #for g in ast.globals:
        #    result.append(g + ' = None')
        #result.append('')
        
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
        for line in self.emit_to_list():
            out.write(line)
            out.write('\n')
    
    def __init__(self, ast):
        assert not ast.errors, "Cannot emit a syntax tree with errors"
        self.ast = ast
