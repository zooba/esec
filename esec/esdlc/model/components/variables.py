'''Provides the `Variable`, `Group` and `Parameter` objects for the
semantic model.
'''

__all__ = ['Variable', 'Parameter']

class Parameter(object):
    '''Represents a parameter in a function call. Parameters either
    have a name and a value (explicit parameter) or just a name
    (implicit paramter; `value` is ``None``).
    '''
    tag = 'parameter'

    def __init__(self, name_value_pair, span=None):
        self.name, self.value = name_value_pair
        self.span = span
        assert isinstance(self.name, str), "`name` must be `str`, not %s" % self.name

    def __iter__(self):
        yield self.name
        yield self.value

    def __getitem__(self, index):
        if index == 0: return self.name
        if index == 1: return self.value
        raise IndexError()

    def __str__(self):
        if self.value is not None:
            return '%s=%s' % (self.name, self.value)
        else:
            return str(self.name)

    def execute(self, context):
        '''Returns a resolved ``name, value`` pair.'''
        if self.value is not None:
            return (self.name, self.value.execute(context))
        else:
            return (self.name, context.get(self.name, True))

class Variable(object):
    '''Represents a variable in the semantic model. Variables may be
    constant, in which case the `value` member is valid, external, or
    neither. Constant and external variables may not be reassigned.

    Variables cannot share names with instances of `Group`.
    '''
    tag = 'variable'

    def __init__(self, name=None, value=None, external=False, constant=False, span=None):
        self.name = str(name or value)
        self.value = value
        self.external = external
        self.constant = constant
        self.references = []
        self.span = span

    def __str__(self):
        return self.name

    def execute(self, context):
        '''Returns the current value for this variable.'''
        if self.constant:
            return self.value
        else:
            return context[self.name]
