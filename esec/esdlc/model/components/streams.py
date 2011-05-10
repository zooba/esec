'''Provides stream objects for the semantic model.
'''

__all__ = ['Stream', 'Operator', 'Merge', 'Join', 'Store', 'EvalStmt', 'YieldStmt']

import itertools
from esdlc.errors import RepeatedDestinationGroupError, RepeatedGroupError
from esdlc.model.components.lists import GroupList, FunctionList

class Stream(object):
    '''Represents a stream.'''
    tag = 'stream'

    def __init__(self, source):
        self.source = source
    
    def __str__(self):
        return str(self.source)
    
    def execute(self, context):
        '''Executes the stream in the provided `context`.'''
        return self.source.execute(context)

class Operator(object):
    '''Represents an operation performed on a single `Stream`.'''
    tag = 'operator'

    def __init__(self, source, func):
        self.source = source
        self.func = func

    def __str__(self):
        return '%s<%s>' % (self.func, self.source)

    def execute(self, context):
        '''Executes the operator in the provided `context`.'''
        return self.func.execute(context, _source=self.source.execute(context))

class Merge(object):
    '''Represents concatenation of multiple instances of `Stream`.'''
    tag = 'merge'

    def __init__(self, sources):
        self.sources = GroupList(sources, allow_generators=True, allow_streams=True)

    def __str__(self):
        return '+'.join(str(i) for i in self.sources)

    def execute(self, context):
        '''Executes the merge in the provided `context`.'''
        return itertools.chain.from_iterable(i.execute(context) for i in self.sources)

class Join(object):
    '''Represents an arbitrary composition of multiple instances of
    `Stream`. The connected `Operator` must be aware of the
    composition.
    '''
    tag = 'join'
    
    def __init__(self, sources):
        self.sources = GroupList(sources, allow_generators=True, allow_streams=True)

    def __str__(self):
        return '&'.join(str(i) for i in self.sources)

    def execute(self, context):
        '''Executes the join in the provided `context`.'''
        return [i.execute(context) for i in self.sources]

class Store(object):
    '''Represents storage of part or all of a `Stream` into one or more
    groups.
    '''
    tag = 'store'
    
    def __init__(self, source, destinations):
        self.source = source
        self.destinations = GroupList(destinations, allow_sizes=True, repeats_error=RepeatedDestinationGroupError)
        self._cached_str = None

    def __str__(self):
        if self._cached_str: return self._cached_str
        
        from_cmd = 'FROM '
        select_cmd = ' SELECT '
        dest_str = str(self.destinations)

        ops = []
        op = self.source
        while isinstance(op, (Stream, Operator)):
            if isinstance(op, Operator):
                ops.append(op.func)
            op = op.source
        ops.reverse()
        op_str = str(FunctionList(ops))

        if isinstance(op, Join):
            from_cmd, select_cmd = 'JOIN ', ' INTO '
            src_str = str(op.sources)
        elif isinstance(op, Merge):
            src_str = str(op.sources)
        else:
            src_str = str(op)

        if op_str:
            return from_cmd + src_str + select_cmd + dest_str + ' USING ' + op_str
        else:
            return from_cmd + src_str + select_cmd + dest_str

    def execute(self, context):
        '''Executes the store in the provided `context`.'''
        source = iter(self.source.execute(context))
        for dest in self.destinations:
            if dest.limit:
                dest.execute(context)[:] = itertools.islice(source, dest.limit.execute(context))
            else:
                dest.execute(context)[:] = source

class EvalStmt(object):
    '''Represents an ``EVAL`` statement for one or more groups.'''
    tag = 'evalstmt'

    def __init__(self, sources, evaluators):
        self.sources = GroupList(sources, repeats_error=RepeatedGroupError)
        if evaluators:
            self.evaluators = FunctionList(evaluators)
        else:
            self.evaluators = None

    def __str__(self):
        if self.evaluators:
            return 'EVAL %s USING %s' % (self.sources, self.evaluators)
        else:
            return 'EVAL %s' % self.sources

    def execute(self, context):
        '''Executes this statement in the current `context`.'''
        raise NotImplementedError()

class YieldStmt(object):
    '''Represents a yield of one or more groups.'''
    tag = 'yieldstmt'

    def __init__(self, sources):
        self.sources = GroupList(sources, repeats_error=RepeatedGroupError)

    def __str__(self):
        return 'YIELD %s' % self.sources

    def execute(self, context):
        '''Executes ``context['_on_yield'](group)`` for each group
        specified in ``self.sources``.
        '''
        _on_yield = context['_on_yield']
        for group in self.sources.execute(context):
            _on_yield(group)
