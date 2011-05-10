'''Provides the `RepeatBlock` object for the semantic model.
'''

__all__ = ['RepeatBlock']

class RepeatBlock(object):
    '''Represents a repeated block of statements.'''
    tag = 'repeatblock'

    def __init__(self, statements, count):
        self.statements = statements
        self.count = count

    def __str__(self):
        return 'REPEAT %s' % self.count

    def execute(self, context):
        '''Executes the block in the provided `context`.'''
        for stmt in self.statements:
            stmt.execute(context)