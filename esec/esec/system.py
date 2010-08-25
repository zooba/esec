'''Implementation of Evolutionary Systems Definition Language (ESDL)
for fully customisable breeding systems.
'''

from esec.utils import ConfigDict, cfg_validate, merge_cls_dicts
import sys, random, traceback

from esec.compiler import Compiler
from esec.monitors import MonitorBase
from esec.individual import Individual, OnIndividual
from esec.generators import selectors, recombiners, joiners
from esec.species import SPECIES

class System(object):
    '''Provides a system using a dynamically generated controller.
    '''
    
    syntax = {
        'system': {
            # The textual description of the system using ESDL
            'definition': str,
            # The object to report to
            '_monitor?': MonitorBase,
            # The type (constructor) to use for building group objects.
            '_group': '*',
            # The default evaluator (must have a method eval(self, individual))
            '_evaluator': '*',
        }
    }
    
    default = {
        'system': {
            '_group': list,
            
            'select_all':       selectors.All,
            'repeat':           selectors.Repeat,
            'best_only':        selectors.BestOnly,
            'worst_only':       selectors.WorstOnly,
            'best':             selectors.Best,
            'worst':            selectors.Worst,
            'truncate_best':    selectors.Best,
            'truncate_worst':   selectors.Worst,
            'unique':           selectors.Unique,
            'best_of_tuple':    selectors.BestOfTuple,

            'tournament':           selectors.Tournament,
            'binary_tournament':    selectors.BinaryTournament,
            'uniform_random':       selectors.UniformRandom,
            'uniform_shuffle':      selectors.UniformRandomWithoutReplacement,
            
            'fitness_proportional': selectors.FitnessProportional,
            'rank_proportional':    selectors.RankProportional,
            'fitness_sus':          selectors.FitnessProportionalSUS,
            'rank_sus':             selectors.RankProportionalSUS,
            
            
            'crossover_uniform':        OnIndividial('crossover_uniform', recombiners.Uniform),
            'crossover_one':            OnIndividual('crossover_one', recombiners.OnePointSame),
            'crossover_one_different':  OnIndividual('crossover_one_different', recombiners.OnePointDifferent),
            'crossover_tuple':          OnIndividual('crossover_tuple', recombiners.PerGeneTuple),
            
            'OnIndividual':     OnIndividual,  # for in-definition specifications
            'mutate_random':    OnIndividual('mutate_random'),
            'mutate_bitflip':   OnIndividual('mutate_bitflip'),
            'mutate_inversion':     OnIndividual('mutate_inversion'),
            'mutate_gap_inversion': OnIndividual('mutate_gap_inversion'),
            'mutate_delta':     OnIndividual('mutate_delta'),
            'mutate_gaussian':  OnIndividual('mutate_gaussian'),
            'mutate_insert':     OnIndividual('mutate_insert'),
            'mutate_delete':     OnIndividual('mutate_delete'),
            
            '_default_join':    joiners.All,    # key is hard-coded in compiler.py
            'full_combine':     joiners.All,
            'best_with_rest':   joiners.BestWithAll,
            'tuples':           joiners.Tuples,
            'random_tuples':    joiners.RandomTuples,
            'distinct_random_tuples': joiners.DistinctRandomTuples,
        }
    }
    
    
    def __init__(self, cfg, lscape=None):
        # Merge syntax and default details
        self.syntax = merge_cls_dicts(self, 'syntax')
        self.cfg = ConfigDict(merge_cls_dicts(self, 'default'))
        # Now apply user cfg details and test against syntax
        self.cfg.overlay(cfg)
        # If no default evaluator has been provided, use `lscape`
        if '_evaluator' not in self.cfg.system:
            self.cfg.system['_evaluator'] = lscape
        cfg_validate(self.cfg, self.syntax, type(self), warnings=False)
        
        # initialise the execution context
        rand = random.Random(cfg.random_seed)
        notify = self._do_notify
        self._context = context = {
            'cfg': self.cfg,
        }
        overrides = self.cfg.system.as_dict()
        context.update(overrides)
        
        for cls in SPECIES:
            inst = context[cls.name] = cls(self.cfg, context['_evaluator'])
            if hasattr(inst, 'public_context'):
                context.update(inst.public_context)
        
        self.definition = self.cfg.system.definition
        compiler = Compiler(self.definition)
        compiler.compile()
        
        # Put our globals into _globals so they appear in every module.
        context['_globals'] = {
            'rand': rand,
            'notify': notify,
            'context': context
        }
        
        self._code_string = compiler.code
        
        self.monitor = context.get('_monitor', MonitorBase())
        context['_on_yield'] = lambda name, group: self.monitor.on_yield(self, name, group)
        
        self._code = compile(self._code_string, 'ESDL Definition', 'exec')
        
        self._in_step = False
        self._continue_step = False
    
    def _do_notify(self, sender, name, value):
        '''Queues a message for the current monitor.
        
        The message consists of a string `name` and an object `value`.
        The sender is either a string or an object reference identifying
        the source of the message.
        
        For example, a mutation operator may include::
            
            notify("mutate_random", "population", 10)
        
        to indicate that ten members of ``population`` were mutated.
        '''
        self.monitor._on_notify(sender, name, value)    #pylint: disable=W0212
    
    def info(self, level):
        '''Report the current configuration.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          level : int |ge| 0
            The verbosity level.
        '''
        result = ['>> System']
        if level > 0:
            result.append('>> Definition:')
            result.append(self.definition.strip(' \t').strip('\n'))
            result.append('')
        if level > 3:
            result.append('>> Compiled Code:')
            result.append(self._code_string)
            result.append('')
        if level > 2:
            result.append('>> ESDL cfg instance:')
            result.extend(self.cfg.list())
        return result
    
    def seed_offset(self, offset):
        '''Re-seed the random instance (shared everywhere) with an offset amount.
        Can be called before each ``run()`` for repeatable variation.
        '''
        seed = self.cfg.random_seed
        self._context['rand'].seed(seed + offset)
        print '>> New Seed: %d + %d (offset)' % (seed, offset)
    
    def begin(self):
        '''Begins the system. Each call to `step` executes one generation.
        '''
        # Allowed to use exec
        #pylint: disable=W0122
        
        try:
            self.monitor.on_run_start(self)
            self.monitor.on_pre_reset(self)
            
            Individual.reset_birthday()
            exec self._code in self._context
            
            self.monitor.on_post_reset(self)
        except KeyboardInterrupt:
            raise
        except:
            ex = sys.exc_info()
            ex_type, ex_value = ex[0], ex[1]
            ex_trace = ''.join(traceback.format_exception(*ex))
            self.monitor.on_exception(self, ex_type, ex_value, ex_trace)
            self.monitor.on_post_reset(self)
            self.monitor.on_run_end(self)
            return
    
    def step(self, block="generation"):
        '''Executes one generation.
        
        :Parameters:
          block : string [optional]
            The name of the block to execute. By default, this is ``generation`` for
            compatibility with earlier definitions. This name is not case-sensitive:
            it is converted to lowercase before use.
        '''
        # Allowed to use exec
        #pylint: disable=W0122
        
        if self._in_step:
            # Detect calls to step() from a callback and handle it
            self._continue_step = True
            return
        
        self._in_step = True
        
        self._continue_step = True
        while self._continue_step:
            # _continue_step may be set by a callback
            self._continue_step = False
            try:
                self.monitor.on_pre_breed(self)
                
                exec ('_block_%s()' % block.lower()) in self._context
            
            except KeyboardInterrupt:
                self.monitor.on_run_end(self)
                raise
            except:
                ex = sys.exc_info()
                ex_type, ex_value = ex[0], ex[1]
                ex_trace = ''.join(traceback.format_exception(*ex))
                self.monitor.on_exception(self, ex_type, ex_value, ex_trace)
            
            self.monitor.on_post_breed(self)
        
        self._in_step = False
    
    def close(self):
        '''Executes clean-up code.
        '''
        self.monitor.on_run_end(self)
