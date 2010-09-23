''':summary: The collection of evaluation landscapes.

.. include:: epydoc_include.txt
.. packagetree:: landscape
   :style: UML

|esec| systems use a concept of *evaluators*, which are object instances
providing an ``eval(individual)`` method that returns the fitness of the
individual. Since evaluators are object instances, they may use parameters
that persist between generations.

The `Landscape` base class provides a rich syntax and parameter validation
system that simplifies the design of evaluators. It is intended for
evaluators that are constructed once prior to an experiment; evaluators
that are constructed each generation should use a more light-weight
approach.

Using `Landscape`
-----------------

Subclasses of `Landscape` *must* call `Landscape.__init__` with all
appropriate parameters. (In particular, the ``cfg`` and ``**other_cfg``
parameters are treated differently to each other and are not
interchangeable.)

`Landscape.__init__` performs the following functions:

- The ``syntax`` dictionary from *all* subclasses are found and overlaid on
  each other, in order, so that a complete syntax is ready for validation
  testing
- The ``default`` dictionary from *all* subclasses are found and overlaid on
  each other, in order, so that a complete set of default values is available
  The supplied configuration (``cfg``) is overlaid on top last.
- Any named parameters (``**other_cfg``) override members of the
  configuration. Underscore characters in parameter names are interpreted as
  periods for the purpose of nesting/recursion into the configuration.
- The configuration is tested in two ways: firstly validated against the
  (combined) syntax and then strict tested against the ``strict`` tuple
  of the instance class. (``strict`` is only of the instance class; it is
  not merged as ``syntax`` and ``default`` are).
- The processed ``cfg`` (if it passes validation) is assigned to ``self.cfg``
  for later use.
- A seeded random instance it stored in ``self.rand``.
- The ``cfg.invert`` and ``cfg.offset`` are stored in ``self.invert`` and
  ``self.offset`` respectively.
- The ``cfg.size`` dictionary is validated and stored in ``self.size.min``,
  ``self.size.max`` and (if applicable) ``self.size.exact``. If
  ``size_equals_parameters`` is ``True`` and ``cfg.parameters`` is provided,
  the value of ``cfg.parameters`` is used for ``self.size.exact``.
- If a ``self._eval`` method has been defined in the subclass, it is bound to
  the instance attribute ``self.eval`` through a function that wraps the
  returned fitness in a `FitnessMaximise` or `FitnessMinimise` class, depending
  on the value of ``maximise``.

The only requirement of a subclass is that it defines an ``_eval()`` method and
calls the `Landscape` initialiser.

'''

import random
from sys import maxint
from random import Random
from esec.fitness import Fitness, FitnessMaximise, FitnessMinimise
from esec.utils import ConfigDict, merge_cls_dicts, cfg_validate, cfg_strict_test
from esec.utils import a_or_an
from types import ModuleType as module

#==============================================================================
# Landscape - Abstract base class for parameterised evaluators.
#==============================================================================

class Landscape(object):
    '''Abstract base class for parameterised evaluators.
    
    See `landscape` for information on how the `Landscape` class assists
    with evaluator implementation.

    See derived classes for more details, or the landscape testing code
    to see how ``test_key`` and ``test_cfg`` are used for.
    '''

    ltype = '--base--' # problem type base classes should set this
    lname = '--none--' # problem type subclasses should overwrite this
    
    maximise = True # is the default objective maximise? (ie fitness)
    size_equals_parameters = True # should size.exact == parameters?
    syntax = { # configuration syntax key's and type. MERGED
        'class?': type, # specific class of landscape
        'instance?': '*', # landscape instance
        'random_seed': [None, int], # for random number instance (if used)
        'invert?': bool,
        'offset?': float,
        'parameters': [None, int],   # may be used by subclasses
        'size': {           # size should be used for all genome size references
            'min': int,
            'max': int,
            'exact': int
        },
    }
    default = { # default syntax values. MERGED
        'random_seed': 12345,
        'invert': False,
        'offset': 0.0,
        'parameters': None,
        'size': {
            'min': 0,
            'max': 0,
            'exact': 0
        },
    }
    
    test_key = () # test keys used for linear configuration strings
    test_cfg = () # tuple of linear configuration strings
    
    strict = {} # eg. 'size.exact':2  <- NOT merged like syntax/default
    
    def __init__(self, cfg=None, **other_cfg):
        self.syntax = merge_cls_dicts(self, 'syntax') # all in hierarchy
        self.cfg = ConfigDict(merge_cls_dicts(self, 'default'))
        
        self.cfg.overlay(cfg)
        for key, value in other_cfg.iteritems():
            if key in self.syntax:
                self.cfg.set_by_name(key, value)
            elif key.partition('_')[0] in self.syntax:
                self.cfg.set_by_name(key.replace('_', '.'), value)
        
        cfg_validate(self.cfg, self.syntax, self.ltype + ':' + self.lname)
        
        # Initialise size properties
        self.size = self.cfg.size
        if self.size_equals_parameters and self.cfg.parameters: self.size.exact = self.cfg.parameters
        if self.size.exact: self.size.min = self.size.max = self.size.exact
        if self.size.min >= self.size.max: self.size.exact = self.size.max = self.size.min
        
        # Now check for any strict limits (ie parameters)
        cfg_strict_test(self.cfg, self.strict)
        
        # random seed?
        if not isinstance(self.cfg.random_seed, int):
            random.seed()
            self.cfg.random_seed = cfg.random_seed = random.randint(0, maxint)
        self.rand = Random(self.cfg.random_seed)
        
        # inversion? offset?
        self.invert = self.cfg.invert
        self.offset = self.cfg.offset
        
        # Autobind _eval_minimise or _eval_maximise.
        if not hasattr(self, 'eval'):
            if self.maximise == self.invert:
                self.eval = self._eval_minimise
            else:
                self.eval = self._eval_maximise
    
    def _eval_maximise(self, indiv):
        '''Evaluates the provided individual and wraps the result in a
        `FitnessMaximise` object.
        '''
        fitness = self._eval(indiv)     #pylint: disable=E1101
        if isinstance(fitness, Fitness): return fitness
        else: return FitnessMaximise(fitness + self.offset)
    
    def _eval_minimise(self, indiv):
        '''Evaluates the provided individual and wraps the result in a
        `FitnessMinimise` object.
        '''
        fitness = self._eval(indiv)     #pylint: disable=E1101
        if isinstance(fitness, Fitness): return fitness
        else: return FitnessMinimise(fitness + self.offset)
    
    @classmethod
    def by_cfg_str(cls, cfg_str):
        '''Used by test framework to initialise a class instance using a simple
        test string specified in each class.test_cfg as nested tuples.
        
        :rtype: Landscape
        '''
        # create ConfigDict using cfg_str (defaults not needed but why not)
        cfg = ConfigDict()
        # map string to appropriate keys and types (or nested keys)
        cfg.set_linear(cls.test_key, cfg_str)
        # provide a new instance
        return cls(cfg)
    
    def info(self, level):
        '''Return landscape info for any landscape
        '''
        result = ['Using %s %s landscape' % (a_or_an(self.lname), self.lname)]
        if level > 3:
            result.append('')
            result.append('Configuration:')
            result.extend(self.cfg.lines())
        return result


#==============================================================================
# Expose landscapes by names and provide easy landscape load(cfg)
#==============================================================================

from esec.utils import cfg_read

LANDSCAPES = []
'''An automatically generated list of the available landscape types.'''

def _do_import():
    '''Automatically populates LANDSCAPES with all the modules in the folder.
    
    :Note: Written as a function to prevent local variables from being imported.'''
    import os
    
    for _, _, files in os.walk(__path__[0]):
        for fname in (file for file in files if file[0] != '_' and file[-3:] == '.py'):
            fname = fname[:fname.find('.')]
            mod = __import__(fname, globals(), fromlist=[])
            for cls in (getattr(mod, s) for s in dir(mod)):
                # Must be a type
                if not type(cls) is type: continue
                # Must derive from Landscape
                if not issubclass(cls, Landscape): continue
                # Must not be landscape
                if cls is Landscape: continue
                # Must have eval methods
                if not hasattr(cls, '_eval') and not hasattr(cls, '_eval_invert'): continue
                # All good
                LANDSCAPES.append(cls)

_do_import()
