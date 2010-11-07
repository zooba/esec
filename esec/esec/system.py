'''Implementation of Evolutionary Systems Definition Language (ESDL)
for fully customisable breeding systems.
'''

import sys, random, traceback
from warnings import warn
from esec.utils import ConfigDict, cfg_validate, merge_cls_dicts
from esec.utils.exceptions import EvaluatorError

from esec.compiler import Compiler
from esec.monitors import MonitorBase
from esec.individual import Individual, OnIndividual
from esec.generators import selectors, recombiners, joiners
from esec.species import SPECIES

from esec.context import _context as global_context

class System(object):
    '''Provides a system using a dynamically generated controller.
    '''
    
    syntax = {
        'system': {
            # The textual description of the system using ESDL
            'definition': str,
            # The object to report to
            '_monitor?': MonitorBase,
            # The default evaluator (must have a method eval(self, individual))
            '_evaluator': '*',
        },
        # The block selector (must support iter(selector))
        'selector?': '*'
    }
    
    default = {
        'system': {
            'select_all':           selectors.All,
            'repeated':             selectors.Repeat,
            'best_only':            selectors.BestOnly,
            'worst_only':           selectors.WorstOnly,
            'best':                 selectors.Best,
            'worst':                selectors.Worst,
            'truncate_best':        selectors.Best,
            'truncate_worst':       selectors.Worst,
            'unique':               selectors.Unique,
            'best_of_tuple':        selectors.BestOfTuple,
            
            'tournament':           selectors.Tournament,
            'binary_tournament':    selectors.BinaryTournament,
            'uniform_random':       selectors.UniformRandom,
            'uniform_shuffle':      selectors.UniformRandomWithoutReplacement,
            
            'fitness_proportional': selectors.FitnessProportional,
            'rank_proportional':    selectors.RankProportional,
            'fitness_sus':          selectors.FitnessProportionalSUS,
            'rank_sus':             selectors.RankProportionalSUS,
            
            
            'crossover':                OnIndividual('crossover', recombiners.Same),
            'crossover_different':      OnIndividual('crossover_different', recombiners.Different),
            'crossover_uniform':        OnIndividual('crossover_uniform', recombiners.Uniform),
            'crossover_discrete':       OnIndividual('crossover_discrete', recombiners.Discrete),
            'crossover_one':            OnIndividual('crossover_one', recombiners.SingleSame),
            'crossover_one_different':  OnIndividual('crossover_one_different', recombiners.SingleDifferent),
            'crossover_two':            OnIndividual('crossover_one', recombiners.DoubleSame),
            'crossover_two_different':  OnIndividual('crossover_one_different', recombiners.DoubleDifferent),
            'crossover_segmented':      OnIndividual('crossover_segmented', recombiners.Segmented),
            'crossover_tuple':          OnIndividual('crossover_tuple', recombiners.PerGeneTuple),
            
            # All other filters are assumed to be OnIndividual
            # and are added to the configuration implicitly.
            
            
            '_default_join':            joiners.Tuples, # key is hard-coded in compiler.py
            'full_combine':             joiners.All,
            'best_with_rest':           joiners.BestWithAll,
            'tuples':                   joiners.Tuples,
            'random_tuples':            joiners.RandomTuples,
            'distinct_random_tuples':   joiners.DistinctRandomTuples,
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
            'config': self.cfg,
            'rand': rand,
            'notify': notify,
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
        
        global_context.context = context
        global_context.config = self.cfg
        global_context.rand = context['rand']
        global_context.notify = context['notify']
        
        self._code_string = compiler.code
        
        self.monitor = context.get('_monitor', None) or MonitorBase()
        self.selector = self.cfg['selector'] or compiler.blocks
        self.selector_current = iter(self.selector)
        context['_on_yield'] = lambda name, group: self.monitor.on_yield(self, name, group)
        
        for var in compiler.uninit:
            if var not in context:
                warn("Variable '%s' is not initialised." % var)
        for func in compiler.filters:
            if func not in context:
                context[func] = OnIndividual(func)
        
        self._code = compile(self._code_string, 'ESDL Definition', 'exec')
        
        self._in_step = False
        self._next_block = [ ]
    
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
        result = []
        if level > 0:
            result.append('>> System Definition:')
            result.append(self.definition.strip(' \t').strip('\n'))
            result.append('')
        if level > 3:
            result.append('>> Compiled Code:')
            result.append(self._code_string)
            result.append('')
        if level > 2:
            result.append('>> Experiment Configuration:')
            result.extend(self.cfg.list())
        if level > 4:
            result.append('>> System context:')
            result.extend(ConfigDict(self._context).list())
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
            if ex[0] is EvaluatorError:
                ex_type, ex_value, ex_trace = ex[1].args
            else:
                ex_type, ex_value = ex[0], ex[1]
                ex_trace = ''.join(traceback.format_exception(*ex))
            self.monitor.on_exception(self, ex_type, ex_value, ex_trace)
            self.monitor.on_post_reset(self)
            self.monitor.on_run_end(self)
            return
    
    def step(self, block=None):
        '''Executes one or more iteration. If `step` is called from the monitor's
        ``on_pre_breed``, ``on_post_breed`` or ``on_exception``, more than one iteration
        will occur. Otherwise, only one iteration will be executed.
        
        :Parameters:
          block : string [optional]
            The name of the block to execute. If specified, the block is used for
            every iteration executed. If omitted, the block selector associated
            with the system is queried for each iteration.
            
            This name is not case-sensitive: it is converted to lowercase before use.
        '''
        self._next_block.append(block)
        
        if self._in_step:
            # If step() has been called from one of our own callbacks, we should
            # return now and let the while loop below pick up the next block.
            return
        
        try:
            self._in_step = True
            while self._next_block:
                # _next_block may be appended to by a callback
                block = self._next_block[0]
                del self._next_block[0]
                
                if block:
                    block_name = str(block).lower()
                elif isinstance(self.selector, list) and len(self.selector) == 1:
                    # Minor performance optimisation for default single block case
                    block_name = str(self.selector[0]).lower()
                else:
                    block_name = None
                
                try:
                    self.monitor.on_pre_breed(self)
                    
                    if not block:
                        block_name = None
                        while not block_name:
                            try:
                                block_name = next(self.selector_current)
                            except StopIteration:
                                self.selector_current = iter(self.selector)
                        block_name = str(block_name).lower()
                    
                    try:
                        exec ('_block_' + block_name + '()') in self._context   #pylint: disable=W0122
                        self.monitor.notify('System', 'Block', block_name)
                    except NameError:
                        if ('_block_' + block_name) not in self._context:
                            # This will be caught immediately and passed to the monitor
                            raise NameError('ESDL block %s is not defined' % block_name)
                        else:
                            raise
                
                except KeyboardInterrupt:
                    self.monitor.on_run_end(self)
                    raise
                except:
                    ex = sys.exc_info()
                    ex_type, ex_value = ex[0], ex[1]
                    ex_trace = ''.join(traceback.format_exception(*ex))
                    self.monitor.on_exception(self, ex_type, ex_value, ex_trace)
                
                self.monitor.on_post_breed(self)
        finally:
            self._in_step = False
    
    def close(self):
        '''Executes clean-up code.
        '''
        self.monitor.on_run_end(self)
