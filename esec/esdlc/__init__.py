'''Provides compilation services for ESDL definitions.

Most users will import the `compileESDL` function and use their own emitter.
'''

import os
import esdlc.ast
import esdlc.model

def compileESDL(source, external_variables=None):
    '''Compiles the provided ESDL definition.
    
    :Parameters:
      source : filename, definition or sequence of strings
        A path to a source file or the source itself. Passing an
        open file object is supported.
      
      external_variables : dictionary of string-value pairs [optional]
        A list of variable names that will be initialised externally.
        Values may be ``None`` if they will be specified later.
    
    :Returns:
        A tuple of the generated semantic model and the validation
        result. If the validation result contains errors, the semantic
        model should not be executed or used to generate code.
    '''
    if isinstance(source, str) and '\n' not in source and os.path.exists(source):
        ast = esdlc.ast.load(source)
    else:
        ast = esdlc.ast.parse(source)
    
    if ast.errors:
        model = None
        validation = esdlc.model.Validator()
        validation._errors.extend(ast._errors)  #pylint: disable=W0212
    else:
        model = esdlc.model.AstSystem(ast=ast, externals=external_variables)
        validation = model.validate()

    return model, validation
