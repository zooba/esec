'''Provides compilation services for ESDL definitions.

Most users will import the `compileESDL` function and use their own emitter.
'''


def compileESDL(source, external_variables=None):
    '''Compiles the provided ESDL definition.
    
    :Parameters:
      source : filename, definition or sequence of strings
        A path to a source file or the source itself. Passing an
        open file object is supported.
      
      external_variables : list of strings [optional]
        A list of variable names that will be initialised externally.
    '''
    import os
    from esdlc.parser import AST
    from esdlc.verifier import Verifier
    
    if isinstance(source, str) and '\n' not in source and os.path.exists(source):
        ast = AST.load(source)
    else:
        ast = AST.parse(source)
    
    if external_variables:
        from esdlc.nodes import VariableNode
        
        externals_list = [VariableNode.define_external(name) for name in external_variables]
        ast.init_block.children[:0] = externals_list
    
    Verifier.run(ast)
    
    return ast
