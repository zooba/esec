'''Emitters are functions (or function-like objects) that convert an
AST into some other form.

Each emitter has a minimum signature:
    
    emit(model, out=sys.stdout, optimise_level=0, profile=False)
    -> (text, context)

where ``text`` may be the output string or ``None``, depending on the
emitter, and ``context`` is an emitter specific value.

``optimise_level`` and ``profile`` are interpreted as suited for each
emitter.
'''