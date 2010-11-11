'''.. include:: epydoc_include.txt

Support functions for the |esec| framework.
'''
import sys, copy, os.path
from itertools import islice
from warnings import warn
from esec.utils.configdict import ConfigDict
from esec.utils.exceptions import ExceptionGroup, UnexpectedKeyWarning

def a_or_an(string):
    '''Returns either 'a' or 'an' depending on the value in `string`.

    This will get a number of cases wrong, but it's better than getting
    most of the cases wrong.
    '''
    if string[0].upper() in ('A', 'E', 'I', 'O', 'U'):
        return 'an'
    else:
        return 'a'

def safe_div(first, second):
    '''Avoid divide-by-zero exceptions. Return 0. Used for reporting.
    '''
    return first / second if second else 0


def settings_split(values):
    '''Split a "settings" string into a dict of long.key.name=value
    pairs. Values are eval()'d to convert them into python types as
    written.
    '''
    if not values: return { }
    bits = [ bit.strip() for bit in values.split(';') ]
    result = { }
    for bit in bits:
        if len(bit) == 0:
            continue
        key, value = bit.split('=')
        result[key] = eval(value)
    return result

def cfg_read(cfg, name, die=False, default=None):
    '''Attempt to read the named property from a dict/ConfigDict
    instance. `name` may be made up of multiple parts, separate by
    periods. This method will navigate nested dictionary objects as
    necessary.
    
    :Returns:
        The value, or `default` if `name` is not found in `cfg`.
    '''
    # Handy nested function
    def get(value, name, default_value):
        '''Extracts a named value from nested dictionary (like) object
        '''
        if not value: return default_value
        bits = name.split('.')
        for bit in bits:
            value = value.get(bit, default_value)
            if not value or value == default_value: break
        return value or default_value
    
    # create sentinel 'default' value
    sentinel = object()
    
    # if needed, extract named value from default
    if isinstance(default, (dict, ConfigDict)):
        default = get(default, name, sentinel)
    
    # extract named value from config cfg
    value = get(cfg, name, sentinel)
    if value is sentinel:
        # missing value? deal with it
        if die or default is sentinel:
            raise ValueError('Missing ' + name)
        else:
            return default
    else:
        return value


def cfg_validate(cfg, syntax, caller='', warnings=True):
    '''Validates `cfg` against the provided syntax.
    
    :Exceptions:
      - `ExceptionGroup`: One or more errors are found.
      - `UnexpectedKeyWarning`: One or more keys were not recognised.
    '''
    errors, warns, other_keys = cfg.validate(syntax)
    if errors: raise ExceptionGroup(caller, errors)
    if warnings:
        for message in warns: warn(message, stacklevel=2)
        if other_keys:
            message = caller + " did not expect configuration keys: " + ', '.join(other_keys)
            warn(message, UnexpectedKeyWarning, stacklevel=2)

def cfg_strict_test(cfg, strict):
    '''Test the cfg for any violations of strict conditions
    '''
    for key, value in strict.items():
        cfg_value = cfg.get_by_name(key)
        if value == '*':
            pass
        elif cfg_value != value:
            raise ValueError("'%s' must be == %s (not %s)" % (key, str(value), str(cfg_value)))

def dict_merge(first, second):
    '''Overlay dict `second` on top of `first`. Useful for merging
    default syntax or configuration data dictionaries
    '''
    result = copy.deepcopy(first)
    if second is not None:
        for key, value in second.iteritems():
            if key in first and isinstance(first[key], dict) and isinstance(value, dict):
                result[key] = dict_merge(first[key], value)
            else:
                result[key] = value
    return result

def get_cls_var(cls, name):
    '''A recursively called function to return a list of the requested
    class level variable (if present) as a list (child-to-parent
    ordered). Absent variables are silently ignored. Root parent class
    MUST derive from ``object``.
    '''
    result = []
    # only if present
    if name in cls.__dict__:
        result = [cls.__dict__[name]]
    # call class parent, but don't go up past "object" class
    if cls.__bases__[0] is not object:
        result.extend(get_cls_var(cls.__bases__[0], name))
    return result

def merge_cls_dicts(obj, name):
    '''Gets all the class dict of the given name in the class hierarchy
    and uses dict_merge() to overlay them (from parent first to child
    last). Returns the combined overlaid dictionary
    '''
    if type(obj) is not type:
        dicts = get_cls_var(type(obj), name)
    else:
        dicts = get_cls_var(obj, name)
    dicts.reverse()
    result = {}
    for i in dicts:
        result = dict_merge(result, i)
    return result


def all_equal(values):
    '''
    :Returns: ``True`` if all elements in `values` are equal; otherwise,
              ``False``.
    '''
    v0 = values[0]
    return all(i == v0 for i in islice(values, 1, None))

def str_short_list(values):
    '''Check if the list is all the same. If so, show a short version.
    [v0, v2, ... vn]
    '''
    if len(values) > 5 and all_equal(values):
        v0 = values[0]
        return '[%s, %s, ... %s] (n=%d)' % (v0, v0, v0, len(values))
    else:
        return str(values)


_is_ironpython = None

def is_ironpython():
    '''
    :Returns: ``True`` if running under IronPython; otherwise,
              ``False``.
    '''
    global _is_ironpython       #pylint: disable=W0603
    if _is_ironpython is None:
        import platform
        try:
            # This will crash when using lib 2.6 on IronPython 2
            if platform.python_implementation() == 'IronPython':
                _is_ironpython = True
            else:
                _is_ironpython = False
        except:     #pylint: disable=W0702
            _is_ironpython = True
    return _is_ironpython
