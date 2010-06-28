'''.. include:: epydoc_include.txt

Contains custom exceptions used in |esec|.
'''

class ESDLSyntaxError(SyntaxError):
    '''Raised when an error is encountered while compiling ESDL code.
    
    Initialiser syntax is ESDLSyntaxError(msg, (filename, lineno, offset, line))
    '''
    pass


class UnexpectedKeyWarning(Warning):
    '''Raised when a key that is passed in a configuration dictionary does not
    appear in the expected syntax.
    '''
    pass


class ExceptionGroup(Exception):
    '''Raised when a group of exceptions have been caught, allowing all errors
    to be passed to a handler rather than only the first.
    '''
    def __init__(self, source, exceptions):
        super(ExceptionGroup, self).__init__()
        self.source = str(source)
        '''A string representing the source of the exceptions in `exceptions`.'''
        self.exceptions = list(exceptions)
        '''The list of exceptions contained in this group.'''
    
    def __str__(self):
        return "Group of exceptions from " + self.source + '\n' + '\n'.join((str(e) for e in self.exceptions))
    
    def __repr__(self):
        return "ExceptionGroup(" + self.source + ',' + ','.join((str(e) for e in self.exceptions)) + ")"
