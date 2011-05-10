'''Provides the `GroupList`, `ParameterList` and `FunctionList` for the
semantic model.
'''
__all__ = ['GroupList', 'ParameterList', 'FunctionList']

class GroupList(list):
    '''Represents a list of groups and generators.'''
    tag = 'grouplist'

    def __init__(self, source, allow_sizes=False, allow_generators=False, allow_streams=False, repeats_error=None):
        super(GroupList, self).__init__(source)
        self.allow_sizes = allow_sizes
        self.allow_generators = allow_generators
        self.allow_streams = allow_streams
        self.repeats_error = repeats_error

    def __str__(self):
        return ', '.join(str(i) for i in self)

    def execute(self, context):
        '''Returns the evaluated members for the given `context`.'''
        return [i.execute(context) for i in self]

class ParameterList(list):
    '''Represents a list of parameters.'''
    tag = 'parameterlist'

    def __str__(self):
        return ', '.join(str(i) for i in self)

    def update(self, source):
        '''Adds the parameters in `source` to this list.'''
        self.extend(source)
    
    @classmethod
    def from_args(cls, **args):
        '''Creates a `ParameterList` from the named arguments provided
        to this method.
        '''
        from esdlc.model.components.variables import Parameter
        return ParameterList(Parameter(i) for i in args.iteritems())

    def execute(self, context):
        '''Returns the evaluated members for the given `context`.'''
        return [i.execute(context) for i in self]


class FunctionList(list):
    '''Represents a list of functions.'''
    tag = 'functionlist'

    def __str__(self):
        return ', '.join(str(i) for i in self)

    def execute(self, context):
        '''Returns the evaluated members for the given `context`.'''
        return [i.execute(context) for i in self]

