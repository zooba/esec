'''Provides `MultiTarget`, a file-like object that distributes any writes
to multiple targets.
'''

class MultiTarget(object):
    '''Provides a file-like object that forwards all writes to multiple
    other file-like objects.
    '''
    def __init__(self, *targets):
        '''Instantiates a new `MultiTarget`.
        
        :Parameters:
          targets : iterable(file-like object)
            A sequence of objects provided ``write`` methods.
        '''
        assert self not in targets, "Cannot include self in targets"
        assert all((hasattr(target, 'write') for target in targets)), "Not all targets have a 'write' method"
        self._targets = list(targets)
    
    def write(self, text):
        '''Posts `text` to the targets given in the constructor.
        '''
        for target in self._targets:
            target.write(text)
    
    def flush(self):
        '''Calls ``flush`` on all targets given in the constructor.
        '''
        def _none():
            '''A 'null' method to simplify the implementation of `flush`.'''
            pass
        for target in self._targets:
            # Use getattr in case ``flush`` is not provided.
            getattr(target, 'flush', _none)()
