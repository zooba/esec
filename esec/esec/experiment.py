'''Provides the `Experiment` class which manages the running of
a single experiment.
'''

from esec.utils import cfg_read, cfg_validate, ConfigDict
from esec.utils.exceptions import ExceptionGroup    #pylint: disable=W0611
from esec.monitors import MonitorBase
from esec.system import System
import esec.landscape as landscape
import random, sys

class Experiment(object):
    '''Used to conduct an experiment using a specified breeding system over
    a given landscape.
    
    This class is instatiated with a dictionary matching `syntax`.
    '''
    
    syntax = {
        'random_seed': [None, int],
        'monitor': '*', # pre-initialised MonitorBase instance, class or dict
        'landscape': '*',
        'system': '*', # allow System to validate
        'verbose': int,
    }
    '''The expected format of the configuration dictionary passed to `__init__`.
    
    .. include:: epydoc_include.txt
    
    Members:
      random_seed : (int or ``None`` [defaults to ``None``])
        The seed value to use for random number generation in the system.
        Landscapes use their own random number generators and must be seeded
        independently.
      
      monitor : (`MonitorBase` instance, subclass or dictionary)
        The monitor to use for the experiment. If it is an instance of a class
        derived from `MonitorBase`, it is used without modification. If it is
        a subclass of `MonitorBase`, it is instantiated with no parameters.
        
        If it is a dictionary, it must have either a key ``instance`` or a key
        ``class``. The ``instance`` key contains an instance of `MonitorBase`.
        The ``class`` key contains a subclass of `MonitorBase` that will be
        instantiated with the relevant configuration dictionary (from ``monitor``
        downwards).
        
        If a valid value is not provided, a `ValueError` is raised.
      
      landscape : (`Landscape` instance, subclass or dictionary)
        The landscape to use for the experiment. If it is an instance of a class
        derived from `Landscape`, it is used without modification. If it is
        a subclass of `Landscape`, it is instantiated with no parameters.
        
        If it is a dictionary, it must have either a key ``instance`` or a key
        ``class``. The ``instance`` key contains an instance of `Landscape`.
        The ``class`` key contains a subclass of `Landscape` that will be
        instantiated with the relevant configuration dictionary (from
        ``landscape`` downwards).
        
        If a valid value is not provided, a `ValueError` is raised.
      
      system : (dictionary)
        The definition of the system. This includes the key ``definition``,
        which is the ESDL text to compile. Any other values provided in
        ``system`` are made available to the system.
        
        Keys in ``system`` should not start with an underscore, since these
        names are reserved for use by the ESDL compiler and runtime.
      
      verbose : (int |ge| 0 [defaults to zero])
        The verbosity level to use.
    
    '''
    
    
    default = {
        'random_seed': None,
        'verbose': 0,
    }
    '''The default values to use for unspecified keys in `syntax`.
    '''
    
    def _load(self, cfg, key, base):
        '''Returns the object provided in `key` of `cfg` if it is derived from
        `base`.
        
        If not, looks for ``instance`` within `key` and returns that. If that
        fails, instantiates ``class`` within `key` with ``cfg.key`` and returns
        that.
        
        If everything fails, returns ``None``.
        '''
        obj = cfg_read(cfg, key)
        if isinstance(obj, base):
            # value is the object
            return obj
        elif isinstance(obj, type) and issubclass(obj, base):
            # value is a class with no configuration
            return obj()
        elif isinstance(obj, (dict, ConfigDict)):
            # try loading .instance
            obj_ins = self._load(cfg, key + '.instance', base)
            if obj_ins: return obj_ins
            # try loading .class (with base == type)
            obj_cls = self._load(cfg, key + '.class', type)
            if obj_cls and issubclass(obj_cls, base):
                # instantiate class with config
                return obj_cls(obj)
        
        # all failed, return None
        return None
    
    def __init__(self, cfg):
        '''Initialises a new experiment with configuration dictionary `cfg`.
        `cfg` must match the syntax given in `syntax`.
        
        :Exceptions:
          - `ValueError`: Unusable values were passed in ``monitor`` or ``landscape``.
            See `syntax` for a description of what constitutes a valid
            value.
          
          - `ExceptionGroup`: One or more unspecified errors were found in `cfg`.
            Access the `ExceptionGroup.exceptions` list to view all
            problems.
        
        '''
        # Configuration processing...
        self.cfg = ConfigDict(self.default)
        # Overlay the supplied cfg onto defaults
        self.cfg.overlay(cfg)
        # -- Validate cfg against syntax
        cfg_validate(self.cfg, self.syntax, 'Experiment', warnings=True)
        
        # hide the user provided cfg with validated self.cfg
        cfg = self.cfg
        
        # -- Monitor --
        self.monitor = self._load(cfg, 'monitor', MonitorBase)
        if not self.monitor: raise ValueError('No monitor provided.')
        cfg.monitor = self.monitor
        
        # random seed?
        self.random_seed = cfg.random_seed
        if not isinstance(self.random_seed, int):
            random.seed()
            self.random_seed = self.cfg.random_seed = random.randrange(0, sys.maxint)
        
        # -- Landscape (of type and name) --
        self.lscape = self._load(cfg, 'landscape', landscape.Landscape)
        cfg.landscape = self.lscape
        
        # -- System --
        self.system = System(cfg, self.lscape)
        self.system.monitor = self.monitor
        
        # -- Pass full configuration to monitor --
        self.monitor.notify('Experiment', 'System', self.system)
        if self.lscape: self.monitor.notify('Experiment', 'Landscape', self.lscape)
        self.monitor.notify('Experiment', 'Configuration', cfg)
    
    
    def run(self):
        '''Run the experiment.
        '''
        self.begin()
        
        while self.step(): pass
        
        self.close()
    
    def begin(self):
        '''Start the experiment.
        '''
        self.system.begin()
    
    def step(self, ignore_monitor=False):
        '''Executes the next step in the experiment. If the monitor's
        ``should_terminate`` callback returns ``True``, the step is not
        executed unless `ignore_monitor` is ``True``.
        
        :Parameters:
          ignore_monitor : bool
            ``True`` to ignore the monitor's ``should_terminate``
            callback.
        
        :Returns:
            ``True`` if the monitor does not indicate that it should
            terminate (that is, ``should_terminate`` returns ``False``).
            This value is unaffected by `ignore_monitor`.
        '''
        
        if self.monitor.should_terminate(self.system):  #pylint: disable=E1103
            if ignore_monitor: self.system.step()
            return False
        else:
            self.system.step()
            return True
    
    def close(self):
        '''Closes the experiment.
        '''
        self.system.close()
        
