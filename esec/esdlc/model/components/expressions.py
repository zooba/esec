'''Provides the `VariableRef`, `GroupRef`, `UnaryOp`, `BinaryOp` and
`Pragma` objects for the semantic model.
'''

__all__ = ['VariableRef', 'GroupRef', 'UnaryOp', 'BinaryOp', 'Pragma']

class VariableRef(object):
    '''Represents a reference to a given variable.'''
    tag = 'variableref'

    def __init__(self, var_id, span=None):
        self.id = var_id
        '''The referenced variable.'''
        self.id.references.append(self)
        self.span = span
        '''A list of tokens constituting this reference.'''

    def __str__(self):
        return str(self.id)

    def execute(self, context):
        '''Returns the current value of this variable.'''
        return self.id.execute(context)

class GroupRef(object):
    '''Represents a reference to a given group.'''
    tag = 'groupref'

    def __init__(self, group_id, limit=None, span=None):
        self.id = group_id
        '''The referenced variable. Groups are stored in non-constant,
        non-internal variables and may be referenced by either
        `GroupRef` or `VariableRef` depending on context.
        '''
        self.limit = limit
        '''The maximum number of individuals to store into this group.
        If not applicable, this should be ``None``.
        '''
        self.id.references.append(self)
        self.span = span
        '''A list of tokens constituting this reference.'''
    
    def __str__(self):
        if self.limit:
            return '(%s) %s' % (self.limit, self.id)
        else:
            return str(self.id)

    def execute(self, context):
        '''Returns the current value of this group.'''
        return self.id.execute(context)

class UnaryOp(object):
    '''Represents an operation on one operand.'''
    tag = 'unaryop'

    def __init__(self, op, right, span=None):
        self.left = None
        '''The left operand. This is always ``None``.'''
        self.op = str(op)
        '''The operator. This must be a string.'''
        self.right = right
        '''The right operand.'''
        self.span = span
        '''A list of tokens constituting this operation.'''

    def __str__(self):
        return '(%s%s)' % (self.op, self.right)

    def execute(self, context):
        '''Executes this operation within the provided `context`.'''
        if self.op == '+':
            return self.right.execute(context)
        elif self.op == '-':
            return -self.right.execute(context)
        else:
            raise TypeError("Unary operator '%s' is not supported." % self.op)

class BinaryOp(object):
    '''Represents an operation on two operands.'''
    tag = 'binaryop'

    def __init__(self, left, op, right, span=None):
        self.left = left
        '''The left operand.'''
        self.op = str(op)
        '''The operator. This must be a string.'''
        self.right = right
        '''The right operand.'''
        self.span = span
        '''A list of tokens constituting this operation.'''
    
    def __str__(self):
        return '(%s%s%s)' % (self.left, self.op, self.right)

    def execute(self, context):
        '''Executes this operation within the provided `context`.'''
        if self.op == '+':
            return self.left.execute(context) + self.right.execute(context)
        elif self.op == '-':
            return self.left.execute(context) - self.right.execute(context)
        elif self.op == '*':
            return self.left.execute(context) * self.right.execute(context)
        elif self.op == '/':
            return self.left.execute(context) / self.right.execute(context)
        elif self.op == '^':
            return self.left.execute(context) ** self.right.execute(context)
        elif self.op == '%':
            return self.left.execute(context) % self.right.execute(context)
        else:
            raise TypeError("Operator '%s' is not supported." % self.op)

class Pragma(object):
    '''Represents an opaque piece of text within a system.'''
    tag = 'pragma'

    def __init__(self, text, span=None):
        self.text = str(text)
        '''The text contained in this pragma, excluding the leading
        backtick. Emitters are responsible for interpreting this text.
        '''
        self.span = span
        '''A list of tokens constituting this pragma.'''

    def __str__(self):
        return '`' + self.text

    def execute(self, context):
        '''Executes this pragma within the provided `context`.'''
        pass