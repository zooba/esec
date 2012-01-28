'''Converts a semantic model to executable Python code.

'''
import itertools
import sys
from warnings import warn

ILLEGAL_VARIABLE_NAMES = frozenset((
    'and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif',
    'else', 'except', 'exec', 'finally', 'for', 'from', 'global', 'globals',
    'if', 'import', 'in', 'is', 'lambda', 'not', 'or', 'pass', 'print',
    'raise', 'return', 'try', 'while', 'with', 'yield'
))

class Profiler(object):
    '''Tracks statement execution time.'''
    def __init__(self):
        self.data = []

    def _current_time(self):
        return 0

    def start(self, statement):
        self.data.append(None)
        self.data[-1] = (statement, 0, self._current_time())

    def end(self, statement):
        self.data.append((statement, 1, self._current_time()))

def _alias(dest, source):
    '''Makes `dest` an alias for `source`. Both are strings.'''
    globals()[dest] = globals()[source]

def _range(count=None):
    '''Returns a sequence of length `count`. If `count` is ``None``,
    returns an empty sequence.
    '''
    return xrange(int(count or 0))

def _part(_source, count=None):
    '''Returns `count` individuals from the beginning of `_source`.
    
    If `count` is ``None``, returns all the individuals in `_source`.
    '''
    if count is None:
        return _source
    else:
        return itertools.islice(_source, int(count))

def _group(_source):
    '''Creates a group from the individuals in `_source`.
    '''
    return [i.born() for i in _source]

def _merge(*_sources):
    '''Returns an iterable sequence of all the individuals in
    `_sources`.
    '''
    def iter_or_call(i):
        '''Returns `i` if it is iterable or ``i()`` otherwise.'''
        try: return iter(i)
        except TypeError: return i()
    
    return itertools.chain.from_iterable(itertools.imap(iter_or_call, _sources))

def _join(*_sources):
    '''Returns a random-access list of the sources provided in
    `_sources`.
    '''
    return list(_sources)


def _evaluator(*_sources):
    '''Returns a suitable evaluator using the elements in `_sources`.
    '''
    def eval_or_call(i):
        '''Returns `i` if it is an instance with an ``eval`` method,
        ``i()`` if it is a class with an ``eval`` method or raises an
        ``AttributeError` if `i` has no ``eval`` method.
        '''
        return i.eval.__self__ or i()
    
    if not _sources: return None
    
    assert len(_sources) == 1, "Only simple evaluators are currently supported"
    return eval_or_call(_sources[0])

def _yield(source_name, source_group):  #pylint: disable=W0613
    '''A placeholder for the ``_yield`` method, which will be specified
    by esec.
    '''
    pass

DEFAULT_CONTEXT = {
    '_alias': _alias,
    '_group': _group,
    '_merge': _merge,
    '_join': _join,
    '_range': _range,
    '_part': _part,
    '_evaluator': _evaluator,
    '_yield': _yield,
}

class _emitter(object): #pylint: disable=R0903
    '''Converts a semantic model to Python code for use with ``esec``.
    '''
    INDENT = '    '

    def __init__(self, model, optimise_level=0, profile=False):
        self.model = model
        self.context = dict(DEFAULT_CONTEXT)
        self.code = []
        self._indent = 0
        self._current_line = None
        self.optimise = optimise_level
        self.profile = profile

        self._wl("_global = globals()")

        for block_name in model.block_names:
            self._emit_block(block_name, model.blocks[block_name])
        
        self._wl("_block_" + model.INIT_BLOCK_NAME + "()")

    def _w(self, obj):  #pylint: disable=C0103
        '''Appends the provided code to the current line.'''
        if self._current_line is None:
            self._current_line = self.INDENT * self._indent
        self._current_line += str(obj)

    def _flush(self):
        '''Writes the current content as a line of code.'''
        if self._current_line is not None:
            self.code.append(self._current_line)
            self._current_line = None

    def _wl(self, obj=None, preflush=False):
        '''Writes a line of code, optionally flushing the previous
        content.
        '''
        if preflush: self._flush()
        if obj is not None:
            self._w(obj)
        if self._current_line is None:
            self._current_line = self.INDENT * self._indent
        self._flush()

    def _emit_block(self, block_name, statements):
        '''Emits code for a named block.'''
        self._wl("def _block_" + block_name.lower() + "():")
        self._indent += 1
        if self.profile:
            self._wl("_profiler.start('BLOCK %s')" % block_name)
            for stmt in statements:
                self._wl("_profiler.start('%s')" % stmt)
                self._emit(stmt)
                self._wl("_profiler.end('%s')" % stmt)
            self._wl("_profiler.end('BLOCK %s')" % block_name)
        else:
            for stmt in statements:
                self._emit(stmt)
        self._indent -= 1
        self._wl()

    def _emit(self, stmt):
        '''Emits code for the provided statement.'''
        tag = stmt.tag
        if self.optimise < 3:
            self._w('# ')
            self._wl(str(stmt))
        if tag == 'repeatblock':
            self._emit_repeat(stmt)
        elif tag == 'function':
            self._emit_function(stmt)
            self._wl()
        elif tag == 'store':
            self._emit_store(stmt)
        elif tag == 'yieldstmt':
            self._emit_yield(stmt)
        elif tag == 'evalstmt':
            self._emit_eval(stmt)
        elif tag == 'pragma':
            self._emit_pragma(stmt)
        else:
            assert False, "Invalid statement: %s" % stmt
        if self.optimise < 3: self._wl()

    def _emit_pragma(self, stmt):
        '''Emits code for pragmas.'''
        if stmt.text and stmt.text.startswith('py '):
            self._wl(stmt.text[3:], preflush=True)

    def _emit_yield(self, stmt):
        '''Emits code for YIELD statements.'''
        self._flush()
        for group in stmt.sources:
            self._w('_yield("')
            self._emit_variable(group.id, name_only=True)
            self._w('", ')
            self._emit_variable(group.id)
            self._wl(')')

    def _emit_eval(self, stmt):
        '''Emits code for EVAL statements.'''
        self._flush()
        if stmt.evaluators:
            self._w('_eval = _evaluator(')
            self._emit_expression(stmt.evaluators[0])
            for evaluator in itertools.islice(stmt.evaluators, 1, None):
                self._w(', ')
                self._emit_expression(evaluator)
            self._wl(')')
        self._w('for _indiv in _merge(')
        self._emit_variable(stmt.sources[0].id)
        for group in itertools.islice(stmt.sources, 1, None):
            self._w(', ')
            self._emit_variable(group.id)
        self._wl('):')
        self._indent += 1
        self._wl('_indiv._eval = _eval')
        self._wl('del _indiv.fitness')
        self._indent -= 1

    def _emit_variable(self, var, name_only=False, safe_access=False):
        '''Emits names for variables.'''
        if name_only:
            self._w(var.name)
        elif var.tag == 'function':
            self._emit_function(var)
        elif var.constant:
            self._w(str(var.value))
        elif safe_access or var.name in ILLEGAL_VARIABLE_NAMES:
            self._w('_global["')
            self._w(var.name)
            self._w('"]')
        else:
            self._w(var.name)

    def _emit_function(self, expr):
        '''Emits code for functions.'''
        if expr.name == '_call':
            self._emit_call(expr)
        elif expr.name == '_alias':
            self._emit_alias(expr)
        elif expr.name == '_assign':
            self._emit_assign(expr)
        elif expr.name == '_getattrib':
            self._emit_getattribute(expr)
        elif expr.name == '_getindex':
            self._emit_getindex(expr)
        else:
            warn("Unhandled function call: %s" % expr.name)

    def _emit_param(self, param):
        '''Emits code for parameter specifications.'''
        self._w(param.name)
        if param.name in ILLEGAL_VARIABLE_NAMES:
            self._w('_')
        self._w('=')
        
        if param.value is None:
            name_lower = param.name.lower()
            var = self.model.variables.get(name_lower) or self.model.externals.get(name_lower)
            if var:
                self._emit_variable(var)
            else:
                self._w('True')
        else:
            self._emit_expression(param.value)

    def _emit_call(self, expr):
        '''Emits code for function calls.'''
        src = next(i.value for i in expr.parameters if i.name == '_function')
        args = [i for i in expr.parameters if i.name != '_function']

        self._emit_expression(src.id)
        self._w('(')
        if args:
            self._emit_param(args[0])
            for arg in itertools.islice(args, 1, None):
                self._w(', ')
                self._emit_param(arg)
        self._w(')')

    def _emit_alias(self, expr):
        '''Emits code for alias statements.'''
        dest = expr.parameter_dict['_destination']
        src = expr.parameter_dict['_source']
        assert dest.tag == 'groupref' and src.tag == 'groupref'

        self._w('_alias("')
        self._emit_variable(dest.id, name_only=True)
        self._w('", "')
        self._emit_variable(src.id, name_only=True)
        self._w('")')

    def _emit_assign(self, expr):
        '''Emits code for assignment statements.'''
        dest = expr.parameter_dict['_destination']
        if dest.tag == 'variableref':
            self._emit_variable(dest.id, safe_access=True)
        else:
            self._emit_expression(dest)
        self._w(' = ')
        self._emit_expression(expr.parameter_dict['_source'])
        
    def _emit_getattribute(self, expr):
        '''Emits code for named attribute access.'''
        self._emit_expression(expr.parameter_dict['_source'])
        self._w('.')
        self._w(expr.parameter_dict['_attrib'])

    def _emit_getindex(self, expr):   
        '''Emits code for indexing.'''     
        self._emit_expression(expr.parameter_dict['_source'])
        self._w('[')
        self._emit_expression(expr.parameter_dict['_index'])
        self._w(']')

    def _emit_expression(self, expr):
        '''Emits code for expressions.'''
        tag = expr.tag
        
        if tag in set(('groupref', 'variableref')):
            self._emit_variable(expr.id)
        elif tag == 'variable':
            self._emit_variable(expr)
        elif tag == 'function':
            self._emit_function(expr)
        elif tag == 'binaryop':
            self._w('(')
            self._emit_expression(expr.left)
            if expr.op == '^':
                self._w('**')
            else:
                self._w(expr.op)
            self._emit_expression(expr.right)
            self._w(')')
        elif tag == 'unaryop':
            self._w('(')
            self._w(expr.op)
            self._emit_expression(expr.right)
            self._w(')')
        else:
            warn("Unhandled expression node %s (%r)" % (expr, expr))

    def _emit_store(self, stmt):
        '''Emits code for Store statements.'''
        if self.optimise > 0:
            self._emit_store_optimised(stmt)
            return

        self._flush()
        
        op = stmt.source
        op_stack = []
        while op.tag not in set(('merge', 'join')):
            op_stack.append(op)
            op = op.source

        self._w("_gen = _" + op.tag + "(")
        self._emit_expression(op.sources[0])
        for group in itertools.islice(op.sources, 1, None):
            self._w(", ")
            self._emit_expression(group)
        self._wl(")")

        if op.tag == 'join' and not op_stack:
            self._wl('_gen = tuples(_source=_gen)')

        while op_stack:
            op = op_stack.pop()
            self._w('_gen = ')
            self._emit_expression(op.func.parameter_dict["_function"])
            self._w('(')
            for arg in (i for i in op.func.parameters if i.name != '_function'):
                self._emit_param(arg)
                self._w(', ')
            self._wl('_source=_gen)')

        for group in stmt.destinations:
            if group.id.tag == 'variable':
                self._emit_variable(group.id, safe_access=True)
            else:
                self._emit_expression(group.id)
            
            if group.limit is None:
                self._wl(' = _group(_gen)')
                break
            else:
                self._w(' = _group(_part(_gen, ')
                self._emit_expression(group.limit)
                self._wl('))')

    def _emit_store_optimised(self, stmt):
        '''Emits optimised code for Store statements.'''
        self._flush()
        
        if len(stmt.destinations) == 1:
            group = stmt.destinations[0]
            if group.id.tag == 'variable':
                self._emit_variable(group.id, safe_access=True)
            else:
                self._emit_expression(group.id)
            self._w(" = _group(")
            if group.limit is not None:
                self._w("_part(")
        else:
            self._w("_gen = ")
        
        closing = ')'
        op = stmt.source
        while op.tag not in set(('merge', 'join')):
            self._emit_expression(op.func.parameter_dict["_function"])
            self._w('(')
            for arg in (i for i in op.func.parameters if i.name != '_function'):
                self._emit_param(arg)
                self._w(', ')
            self._w('_source=')
            closing += ')'
            op = op.source

        if op.tag == 'join' and closing == ')':
            self._w('tuples(_source=')
            closing += ')'

        self._w('_' + op.tag + '(') # either '_merge()' or '_join()'
        self._emit_expression(op.sources[0])
        for group in itertools.islice(op.sources, 1, None):
            self._w(", ")
            self._emit_expression(group)
        self._w(closing)

        if len(stmt.destinations) == 1:
            group = stmt.destinations[0]
            if group.limit is None:
                self._wl(')')
            else:
                self._w(', ')
                self._emit_expression(group.limit)
                self._wl('))')
        else:
            self._wl()
            for group in stmt.destinations:
                if group.id.tag == 'variable':
                    self._emit_variable(group.id, safe_access=True)
                else:
                    self._emit_expression(group.id)
                
                if group.limit is None:
                    self._wl(' = _group(_gen)')
                    break
                else:
                    self._w(' = _group(_part(_gen, ')
                    self._emit_expression(group.limit)
                    self._wl('))')
                    
    def _emit_repeat(self, block):
        '''Emits code for REPEAT blocks.'''
        if (self.optimise > 1 and 
            block.count.tag == 'variableref' and block.count.id.tag == 'variable' and 
            block.count.id.constant and block.count.id.value <= 4):
            for _ in xrange(int(block.count.id.value)):
                for stmt in block.statements:
                    self._emit(stmt)
        else:
            self._w("for _ in _range(")
            self._emit_expression(block.count)
            self._wl("):")
            self._indent += 1
            for stmt in block.statements:
                self._emit(stmt)
            self._indent -= 1

def emit(model, out=sys.stdout, optimise_level=0, profile=False):
    '''Converts the provided model to ``esec`` compatible code.
    '''
    result = _emitter(model, optimise_level, profile)
    if out is not None:
        for line in result.code:
            print >> out, line

    return '\n'.join(result.code), result.context
