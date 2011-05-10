'''.. include:: epydoc_include.txt

Contains custom exceptions used in |esec|.
'''

class UnexpectedKeyWarning(Warning):
    '''Raised when a key that is passed in a configuration dictionary
    does not appear in the expected syntax.
    '''
    pass

class EvaluatorError(Exception):
    '''Raised when an exception occurs within a fitness evaluation.
    
    Because evaluations typically take place within a property getter,
    some exceptions (specifically ``AttributeError``) are treated as a
    missing ``fitness`` property. To avoid this situation, a new error
    is thrown that contains the original.
    '''
    pass

class ESDLCompilerError(Exception):
    '''Raised when a system does not compile.

    The `validation_result` member contains all the errors and warnings
    produced during compilation.
    '''
    def __init__(self, validation_result, *args):
        super(ESDLCompilerError, self).__init__(*args)
        self.validation_result = validation_result

class ExceptionGroup(Exception):
    '''Raised when a group of exceptions have been caught, allowing all
    errors to be passed to a handler rather than only the first.
    '''
    def __init__(self, source, exceptions):
        super(ExceptionGroup, self).__init__()
        self.source = str(source)
        '''A string representing the source of the exceptions in
        `exceptions`.
        '''
        self.exceptions = list(exceptions)
        '''The list of exceptions contained in this group.'''
    
    def __str__(self):
        return "Group of exceptions from " + self.source + '\n' + '\n'.join((str(e) for e in self.exceptions))
    
    def __repr__(self):
        return "ExceptionGroup(" + self.source + ',' + ','.join((str(e) for e in self.exceptions)) + ")"
