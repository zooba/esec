'''Dictionary class that maps object attributes to elements. Getting,
setting or deleting an attribute accesses the underlying dictionary
elements.
'''

class attrdict(dict):
    '''Maps attributes to keys within the dictionary. The ``str`` method
    is overridden to provide more compact output and the `lines` method
    recursively lists the contents of an `attrdict` tree.
    '''
    def __getattr__(self, key):
        if key.startswith('__'): raise AttributeError(key + ' not found')
        return self.__getitem__(key)
    
    def __setattr__(self, key, value):
        if key.startswith('__'): raise AttributeError(key + ' not found')
        self[key] = value
    
    def __delattr__(self, key):
        if key.startswith('__'): raise AttributeError(key + ' not found')
        del self[key]
    
    def __str__(self):
        parts = []
        for key, value in sorted(self.iteritems(), key=lambda item: item[0]):
            parts.append(str(key) + ':' + str(value))
        return '{' + ', '.join(parts) + '}'
    
    def lines(self, prefix='', always_prefix=True, scope_char='.', value_char=' = '):
        '''Returns a sequence of lines containing the complex contents
        of the dictionary. Nested dictionaries are recursed. Lines are
        sorted by key name.
        '''
        for key, value in sorted(self.iteritems(), key=lambda item: item[0]):
            full_key = prefix + str(key)
            
            if isinstance(value, dict) and not hasattr(value, 'lines'):
                value = attrdict(value)
            
            if isinstance(value, attrdict):
                if not always_prefix:
                    yield full_key
                    for line in value.lines(' ' * len(full_key) + scope_char,
                                            always_prefix=always_prefix,
                                            scope_char=scope_char, value_char=value_char):
                        yield line
                else:
                    for line in value.lines(full_key + scope_char,
                                            always_prefix=always_prefix,
                                            scope_char=scope_char, value_char=value_char):
                        yield line
            else:
                yield full_key + value_char + str(value)

