'''Implementation of Evolutionary Systems Definition Language (ESDL)
for fully customisable breeding systems.
'''

import sys, random, traceback
from warnings import warn
from esec.utils import ConfigDict, cfg_validate, merge_cls_dicts
from esec.utils.exceptions import EvaluatorError, ESDLCompilerError

from esdlc import compileESDL
from esdlc.emitters.esec import emit

from esec import GLOBAL_ESDL_FUNCTIONS
from esec.monitors import MonitorBase
from esec.individual import Individual, OnIndividual
import esec.generators  #pylint: disable=W0611
from esec.species import SPECIES

import esec.context

class GroupAlias(object):
    '''Represents an aliased group.'''
    def __init__(self, dest_name, source_name):
        self._source_name = source_name
        esec.context.context[dest_name] = self

    def __len__(self):                  return esec.context.context[self._source_name].__len__()
    def __iter__(self):                 return esec.context.context[self._source_name].__iter__()
    def __getitem__(self, key):         return esec.context.context[self._source_name].__getitem__(key)
    def __setitem__(self, key, value):  return esec.context.context[self._source_name].__setitem__(key, value)

class System(object):
    '''Provides a system using a dynamically generated controller.
    '''
    
    syntax = {
        'system': {
            # The textual description of the system using ESDL
            'definition': str,
        },
        # The block selector (must support iter(selector))
        'selector?': '*'
    }
    
    default = {
        'system': {
            # Filters are specified using esdl_func for unbound
            # functions or public_context when bound to a species.
            # All other filters are assumed to be OnIndividual and are
            # included implicitly.
        }
    }
    
    
    def __init__(self, cfg, lscape=None, monitor=None):
        # Merge syntax and default details
        self.syntax = merge_cls_dicts(self, 'syntax')
        self.cfg = ConfigDict(merge_cls_dicts(self, 'default'))
        # Merge in all globally defined ESDL functions
        for key, value in GLOBAL_ESDL_FUNCTIONS.iteritems():
            self.cfg.system[key.lower()] = value
        # Now apply user cfg details and test against syntax
        self.cfg.overlay(cfg)
        # If no default evaluator has been provided, use `lscape`
        cfg_validate(self.cfg, self.syntax, type(self), warnings=False)
        
        # Initialise empty members
        self._code = None
        self._code_string = None
        
        self.monitor = None
        self.selector = None
        self.selector_current = None
        
        self._in_step = False
        self._next_block = []
        self._block_cache = {}

        # Compile code
        self.definition = self.cfg.system.definition
        self._context = context = {
            'config': self.cfg,
            'rand': random.Random(cfg.random_seed),
            'notify': self._do_notify
        }
        
        # Add species settings to context
        for cls in SPECIES:
            inst = context[cls.name] = cls(self.cfg, lscape)
            try:
                for key, value in inst.public_context.iteritems():
                    context[key.lower()] = value
            except AttributeError: pass

        # Add external values to context
        for key, value in self.cfg.system.iteritems():
            if isinstance(key, str):
                key_lower = key.lower()
                if key_lower in context:
                    warn("Overriding variable/function '%s'" % key_lower)
                context[key_lower] = value
            else:
                warn('System dictionary contains non-string key %r' % key)
        
        
        model, self.validation_result = compileESDL(self.definition, context)
        if not self.validation_result:
            raise ESDLCompilerError(self.validation_result, "Errors occurred while compiling system.")
        self._code_string, internal_context = emit(model, out=None, optimise_level=0, profile='_profiler' in context)
        
        internal_context['_yield'] = lambda name, group: self.monitor.on_yield(self, name, group)
        internal_context['_alias'] = GroupAlias
        
        for key, value in internal_context.iteritems():
            if key in context:
                warn("Variable/function '%s' is overridden by internal value" % key)
            context[key] = value

        esec.context._context.context = context
        esec.context._context.config = context['config']
        esec.context._context.rand = context['rand']
        esec.context._context.notify = context['notify']
        
        self.monitor = monitor or MonitorBase()
        self.selector = self.cfg['selector'] or [name for name in model.block_names if name != model.INIT_BLOCK_NAME]
        self.selector_current = iter(self.selector)
        
        for func in model.externals.iterkeys():
            if func not in context:
                context[func] = OnIndividual(func)
        
        self._code = compile(self._code_string, 'ESDL Definition', 'exec')
    
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
        '''Re-seed the random instance (shared everywhere) with an
        offset amount. Can be called before each ``run()`` for
        repeatable variation.
        '''
        seed = self.cfg.random_seed
        self._context['rand'].seed(seed + offset)
        print '>> New Seed: %d + %d (offset)' % (seed, offset)
    
    def begin(self):
        '''Begins the system. Each call to `step` executes one
        generation.
        '''
        # Allowed to use exec
        #pylint: disable=W0122
        
        try:
            self.monitor.on_run_start(self)
            self.monitor.on_pre_reset(self)
            
            # Reset the birthday counter
            Individual.reset_birthday()
            
            # Reset the block invocation cache
            self._block_cache = { }
            
            # Reset externally specified variables
            inner_context = self._context
            for key in self.cfg.system.iterkeys():
                key_lower = key.lower()
                if key_lower in inner_context:
                    inner_context[key_lower] = self.cfg.system[key]
            
            # Run the initialisation block
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
        '''Executes one or more iteration. If `step` is called from the
        monitor's ``on_pre_breed``, ``on_post_breed`` or
        ``on_exception``, more than one iteration will occur. Otherwise,
        only one iteration will be executed.
        
        :Parameters:
          block : string [optional]
            The name of the block to execute. If specified, the block is
            used for the first iteration executed. If omitted, the block
            selector associated with the system is queried for each
            iteration.
            
            This name is not case-sensitive: it is converted to
            lowercase before use.
        '''
        self._next_block.append(block)
        
        if self._in_step:
            # If step() has been called from one of our own callbacks,
            # we should return now and let the while loop below pick up
            # the next block.
            return
        
        try:
            self._in_step = True
            while self._next_block:
                # _next_block may be appended to by a callback
                block = self._next_block.pop(0)
                
                if block:
                    block_name = str(block).lower()
                elif isinstance(self.selector, list) and len(self.selector) == 1:
                    # Performance optimisation for default single block case
                    block_name = str(self.selector[0]).lower()
                else:
                    block_name = None
                
                try:
                    self.monitor.on_pre_breed(self)
                    
                    if block_name is None:
                        try:
                            block_name = next(self.selector_current)
                        except StopIteration:
                            self.selector_current = iter(self.selector)
                            block_name = next(self.selector_current)
                        block_name = str(block_name).lower()
                    
                    try:
                        codeobj = self._block_cache.get(block_name)
                        if codeobj is None:
                            codeobj = compile('_block_' + block_name + '()', 'Invoke ' + block_name, 'exec')
                            self._block_cache[block_name] = codeobj
                        exec codeobj in self._context   #pylint: disable=W0122
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
        '''Executes clean-up code.'''
        self.monitor.on_run_end(self)