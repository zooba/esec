'''Provides the `Variable` and `Parameter` objects for the semantic
model.
'''

__all__ = ['Variable', 'Parameter']

class Parameter(object):
    '''Represents a parameter in a function call. Parameters either
    have a name and a value (explicit parameter) or just a name
    (implicit paramter; `value` is ``None``).
    '''
    tag = 'parameter'

    def __init__(self, name_value_pair, span=None):
        self.name = name_value_pair[0]
        '''The parameter name. This must be a string.'''
        self.value = name_value_pair[1]
        '''The parameter value. This may be ``None`` to indicate an
        implicit parameter.
        '''
        self.span = span
        '''A list of the tokens constituting this parameter.'''
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
    '''
    tag = 'variable'

    def __init__(self, name=None, value=None, external=False, constant=False, span=None):
        self.name = str(name or value)
        '''The name of the variable. For anonymous constants, this is
        a string representation of `value`.
        '''
        self.value = value
        '''The value of the variable. For externals or constants, this
        may not be modified within the system. For other variables,
        this may be ``None``.
        '''
        self.external = external
        '''Indicates that the variable is provided externally to the
        system. External variables cannot be modified within a system.
        '''
        self.constant = constant
        '''Indicates that the variable is a constant. Constants must
        provide a value at compile-time; this value may be substituted
        directly into any generated code.
        '''
        self.references = []
        '''A list of references to this variable.
        '''
        self.span = span
        '''The list of tokens constituting the original definition of
        this variable. Each reference may have its own distinct span.
        '''
        self.alias = None
        '''The original variable aliased by this variable. This is not
        valid except when executing the model.'''

    def __str__(self):
        return self.name

    def execute(self, context):
        '''Returns the current value for this variable.'''
        if self.constant:
            return self.value
        elif self.alias:
            return self.alias.execute(context)
        else:
            return context[self.name]
