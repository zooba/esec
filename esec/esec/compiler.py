'''Provides Evolutionary System Definition Language (ESDL) compilation
and validation.
'''

from warnings import warn
from esec.utils.exceptions import ExceptionGroup
from esdlc import compileESDL
from esdlc.esec import EsecEmitter

class Compiler(object):
    '''Compiles ESDL into Python scripts.
    '''
    
    def __init__(self, src):
        '''Initialises the compiler object but does not perform
        compilation or return any code.
        
        Call `compile` and then obtain executable Python code from
        `code`.
        
        :Parameters:
          src : str
            The ESDL code to compile. This string is stored in
            ``self.source_code`` and may be modified or replaced before
            calling `compile`.
        '''
        self.source_code = src
        '''ESDL system definition to compile. After calling `compile`,
        `code` will contain an executable Python script.
        '''
        
        self.blocks = None
        '''A list of blocks in the order they were specified.'''
        self.filters = None
        '''A list of filters required by the system.'''
        self.externals = [ ]
        '''A list of variables that are initialised externally. This
        should be extended by the caller prior to calling `compile` to
        avoid uninitialised variable warnings and to properly handle
        implicit parameters.
        '''
        self.code = None
        '''Compiled Python code implementing `source_code`.'''
    
    def compile(self):
        '''Compiles the source associated with this compiler object. The
        result is placed in ``self.code`` as a string.
        
        May raise `ExceptionGroup` if there are syntactical errors in
        `source_code`. Further errors may be raised when executing the
        code produced.
        '''
        ast = compileESDL(self.source_code, self.externals)
        if ast.errors:
            raise ExceptionGroup("Compiler", ast.errors)
        for warning in ast.get_warnings():
            warn(str(warning))
        
        self.blocks = [block.name for block in sorted(ast.blocks.itervalues(), key=lambda i: i.index)]
        self.filters = ast.filters
        
        self.code = '\n'.join(EsecEmitter(ast).emit_to_list())
