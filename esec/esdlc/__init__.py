'''Provides compilation services for ESDL definitions.

Most users will import the `compileESDL` function and use their own emitter.
'''


def compileESDL(source):
    '''Compiles the provided ESDL definition.
    
    :Parameters:
      source : filename, definition or sequence of strings
        A path to a source file or the source itself. Passing an
        open file object is supported.
    '''
    import os
    from esdlc.parser import AST
    from esdlc.verifier import Verifier
    
    if '\n' not in source and os.path.exists(source):
        ast = AST.load(source)
    else:
        ast = AST.parse(source)
    
    Verifier.run(ast)
    
    return ast
