'''Provides access to the state of a running experiment from modules outside
the ESDL definition.

Standard usage of this module is to import the required properties, for example::

    from esec.context import rand, notify

The `_context` variable may be imported to share state that does not fit in with
any of the other variables.
'''
import threading
_context = threading.local()
'''The object providing access to the state of the current
ESDL simulation. Access should generally occur by importing
the properties in this module directly.'''

class _context_property(object):    #pylint: disable=R0903
    '''Internal object for providing normal access to the context dictionary.'''
    def __getattr__(self, name): return getattr(_context.context, name)
    def __setattr__(self, name, value): setattr(_context.context, name, value)
    def __getitem__(self, name): return _context.context[name]
    def __setitem__(self, name, value): _context.context[name] = value

class _config_property(object):     #pylint: disable=R0903
    '''Internal object for providing normal access to the configuration
    dictionary.'''
    def __getattr__(self, name): return getattr(_context.config, name)
    def __setattr__(self, name, value): setattr(_context.config, name, value)
    def __getitem__(self, name): return _context.config[name]
    def __setitem__(self, name, value): _context.config[name] = value

class _rand_property(object):       #pylint: disable=R0903
    '''Internal object for providing normal access to the random object.'''
    def __getattr__(self, name): return getattr(_context.rand, name)
    def __setattr__(self, name, value): setattr(_context.rand, name, value)

class _notify_property(object):     #pylint: disable=R0903
    '''Internal object for providing normal access to the ``notify`` method.'''
    def __getattr__(self, name): return getattr(_context.notify, name)
    def __setattr__(self, name, value): setattr(_context.notify, name, value)
    def __call__(self, *p, **kw): return _context.notify(*p, **kw)


context = _context_property()
'''Gets the dictionary containing the system context.
This contains all the names available within the ESDL
definition, as well as any created groups or variables.
'''


config = _config_property()
'''Gets the system-wide random number generator. This
RNG should be used for any operators applied to
individuals for which a random component is required.
'''

rand = _rand_property()
'''Gets the system-wide random number generator. This
RNG should be used for any operators applied to
individuals for which a random component is required.
'''

notify = _notify_property()
'''Gets the notification function for the current
monitor. The actual signature of this function is
given in `esec.monitors.MonitorBase.notify`.
'''
