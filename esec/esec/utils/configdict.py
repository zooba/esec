'''Customised dictionary for nested configuration details and
validation.

The `ConfigDict` class includes the ability to overlay instances,
recursively list keys and values, and be validated against a syntax
dictionary.

This allows several nice features

- specifying modular recombination of configuration through overlaying
  configuration instances. eg. new_cfg = basic_EA + pop_structure + 
  landscape_cfg + ...
- a class can specify its required syntax easily, and easily validate
  that an argument cfg object is valid via a simple central (unified)
  model.
- default values are ``None``
- keys, and nested keys, can be accessed with attribute . notation.

See also `utils.cfg_read()` and `utils.cfg_validate()` which act as
useful in-application support functions.
'''

from esec.utils.attributedict import attrdict

class ConfigDict(attrdict):     #pylint: disable=R0904
    '''A custom dictionary for configuration data that supports:
    
    - default None for empty values (not key error)
    - item key access [key] to values OR
    - attribute key access (.) to values
    - validate-against-dict test useful for checking if key and values
      are of valid name and type. See the `validate` method for details.
    - overlay support to build up larger configurations
    - supports '+' to merge dictionaries or a supported string of
      keys/values.
    - supports set/get by string name for nested items
    - iteration by keys/items
    - dict-list (and print) of all nested keys/values (dict style view)
    - line-list (and print) of all keys/values (per line style view)
    
    '''
    
    def __init__(self, data=None):
        '''Initialise, using optional dictionary, `ConfigDict` or string
        data for key/value data.
        
        String data is of the form ``key=value`` separated by ``;`` and
        values are evaluated to converted them into appropriate types.
        
        For example::
            
            data = "key1.subkey3='Fred'; key2.subkey5=False"
        
        '''
        super(ConfigDict, self).__init__()
        
        if data:
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, dict) and all(isinstance(i, str) for i in value.iterkeys()):
                        value = ConfigDict(value)
                    elif isinstance(value, ConfigDict):
                        value = ConfigDict(value)
                    self[key] = value
            elif isinstance(data, str):
                bits = [bit.strip() for bit in data.split(';')]
                for bit in bits:
                    if len(bit) > 0:
                        name, value = bit.split('=')
                        self.set_by_name(name, eval(value))
    
    
    def validate(self, syntax, scope=''):   #pylint: disable=R0912,R0915
        '''Check internal keys/value type against provided syntax
        
        - Uses a plain dictionary for syntax (supports nesting) for
          valid 'key': [valuetype|dict|(set)|[list]|string]
        - All keys are strings. Missing keys are considered errors
        - Use '?' to indicate optional key eg. ``{'keyname?':str }``
        - Validated valuetypes (str, int, float, bool}
        - Nested dict to contain nested syntax
        - Tuples as string sets for keyword eg. ``('LEFT','RIGHT')``
        - List for a set of valid value types or ``None`` (as a valid
          value)
        - Valuetype '*' indicates any value accepted.
        - Unexpected keys are warnings.
        
        Returns tuple of ``(errors, warnings, unrecognised keys)`` lists
        with ``Exception`` instances, ``UserWarning`` instances or
        key name strings respectively.
        '''
        errors = []
        warnings = []
        unrecognised_keys = []
        
        allkeys = self.keys()
        for key, valuetype in syntax.iteritems():
            
            # check for "?" - an optional key, and strip
            optional = key[-1] == '?'
            if optional:
                key = key[:-1]
            # handy scope+key
            scopekey = scope+key
            
            # check for required key
            if key not in allkeys:
                if not optional:
                    errors.append(KeyError("Missing required key", scopekey))
            
            # Test the key's value (if valuetype is not ignore '*')
            else:
                # mark key as "known", keep value handy
                allkeys.remove(key)
                value = self[key]
                # do we validate?
                if valuetype != '*':
                    # check for nested keys and do recursion check
                    if isinstance(valuetype, dict) and value is not None:
                        err, warns, other_keys = value.validate(valuetype, scopekey + '.')
                        errors.extend(err)
                        warnings.extend(warns)
                        unrecognised_keys.extend(other_keys)
                    # check for valid keyword in tuple
                    elif isinstance(valuetype, tuple):
                        if value not in valuetype:
                            if isinstance(value, float) and int in valuetype:
                                ivalue = int(value)
                                if ivalue != value: warnings.append(UserWarning("Cast '%s' value to int" % scopekey))
                                self[key] = value = ivalue
                            else:
                                errors.append(ValueError("Value '%s' not in %s" % (value, str(valuetype)), scopekey))
                    # check for valid type in a list of types
                    elif isinstance(valuetype, list):
                        # accept None as a type...
                        if None in valuetype:
                            valuetype.append(type(None))
                        # accept ConfigDict's in place of normal dict's
                        if dict in valuetype:
                            valuetype.append(ConfigDict)
                        # handle float/int conversions
                        if isinstance(value, float) and float not in valuetype and int in valuetype:
                            ivalue = int(value)
                            if ivalue != value: warnings.append(UserWarning("Cast '%s' value to int" % scopekey))
                            self[key] = value = ivalue
                        # check the value type...
                        if not isinstance(value, tuple(t for t in valuetype if isinstance(t, type))):
                            errors.append(TypeError("Type '%s' not in %s" % (type(value), str(valuetype)), scopekey))
                    # check for simple valid types (int, str, float etc)
                    elif not isinstance(value, valuetype):
                        # check for simple dictionary type (unspecified content)
                        if valuetype is dict and isinstance(value, (dict, ConfigDict)):
                            continue
                        # handle float/int conversions
                        if valuetype is int and isinstance(value, float):
                            ivalue = int(value)
                            if ivalue != value: warnings.append(UserWarning("Cast '%s' value to int" % scopekey))
                            self[key] = value = ivalue
                            continue
                        # check for literal string match with type
                        if valuetype == value:
                            continue
                        # catch other simple type issues
                        message = "Type '%s' is not '%s'" % (type(value).__name__, valuetype.__name__)
                        errors.append(TypeError(message, scopekey))
        
        # check for unknown keys - possible user typos/errors
        for key in allkeys:
            unrecognised_keys.append(scope + key)
        # share the happy news
        return errors, warnings, unrecognised_keys
    
    
    def __getitem__(self, key):
        '''Item get access. Default to ``None`` if not present.'''
        return self.get(key, None)

    def overlay(self, other):
        '''Overlay the other ConfigDict, dict or appropriate string of
        values onto this instance. If ``other`` is a simple ``dict`` or
        string, try to turn it into `ConfigDict` first.  Anything else
        raises a ``TypeError``.
        
        Nested dictionaries are handled by creating new `ConfigDict`
        instances.
        
        Copies are made of nested `ConfigDict` instances to avoid shared
        reference issues.
        '''
        # silently ignore empty dictionary/None
        if not other:
            return
        # convert suitable dict or strings
        if isinstance(other, (str, dict)):
            other = ConfigDict(other)
        # Enforce other's type is ConfigDict
        if not isinstance(other, ConfigDict):
            raise TypeError("Can only overlay a ConfigDict (or dict) instance")
        # Go through other's items and apply to self, recursively if needed
        for key, value in other.iteritems():
            if isinstance(value, ConfigDict):
                if isinstance(self[key], ConfigDict):
                    self[key].overlay(value)
                else:
                    self[key] = ConfigDict(value)
            else:
                self[key] = value
    
    def as_dict(self):
        '''Return as a simple dict. Nesting is ignored, so any elements
        which are `ConfigDict` instances will not be modified.
        '''
        result = {}
        for key, value in self.iteritems():
            result[key] = value
        return result
    
    def __add__(self, other):
        '''Overlays `other` onto `self`, returning the result.
        `self` is not modified.
        '''
        result = ConfigDict(self)
        result.overlay(other)
        return result
    
    def __iadd__(self, other):
        '''Overlays `other` onto `self`.'''
        self.overlay(other)
        return self
    
    def list(self, indent_level=0):
        '''Returns the keys and values as a list of strings.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          indent_level : int |ge| 0
            The initial indent level to display with. Each indent level
            becomes four spaces at the beginning of each line.
        
        :Returns:
            A list of strings, each element containing one line of
            output.
            
            Use ``'\\n'.join(o.list())`` to print to the console.
        
        '''
        indent = '    ' * indent_level
        result = [indent + '{']
        for key in sorted(self.iterkeys()):
            value = self[key]
            if isinstance(value, ConfigDict):
                result.append(indent + "    '" + key + "': ")
                result.extend(value.list(indent_level + 1))
            else:
                if type(value) is str:
                    value = "'" + value + "'"
                result.append(indent + "    '%s': %s," % (key, value))
        if indent_level:
            result.append(indent + '},')
        else:
            result.append('}')
        return result
    
    
    def set_linear(self, keys, cfg_str):
        '''
        Converts a string of values and maps them to keys of type::
        
            keys = (('name', str), ('size', int), ('flag', bool)
            cfg_str = "fred 10 True"
        
        '''
        bits = cfg_str.split(' ')
        assert len(keys) >= len(bits), "More values than keys!!"
        # set the corresponding key with the converted string value
        for i, value in enumerate(bits):
            if value != '.':
                # name, type = keys[i]
                self.set_by_name(keys[i][0], keys[i][1](value))
    
    def set_by_name(self, name, value):
        '''Set a value using long.dot.name key.'''
        bits = name.split('.')
        target = self
        for key in bits[:-1]:
            if target[key] is None: # create path if needed
                target[key] = ConfigDict()
            target = target[key]
        target[bits[-1]] = value
    
    def get_by_name(self, name):
        '''Get a value using any long.dot.name key.'''
        bits = name.split('.')
        value = self
        for bit in bits:
            value = value[bit]
            if value is None:
                return None
        return value
    
    def savetofile(self, filename, comment=None):
        '''Save all details to text file. A list of comments can also be
        added.
        '''
        target = open(filename, 'w')
        if comment:
            target.write('# '+'\n# '.join(comment)+'\n')
        target.write('config = ')
        for line in self.list():
            target.write(line)
        target.close()
