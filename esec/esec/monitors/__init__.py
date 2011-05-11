'''The default set of monitors.

.. packagetree:: esec.monitors
   :style: UML
'''

from esec.utils import merge_cls_dicts, cfg_validate, ConfigDict

class MonitorBase(object):
    '''Defines the base class for monitors to be used with ESDL defined
    systems.
    
    `MonitorBase` can also be used as a 'do-nothing' monitor.
    
    While `MonitorBase` does not make use of it, configuration
    dictionaries are supported. The default initialiser accepts a
    configuration which it will overlay over child ``syntax`` and
    ``default`` dictionaries.
    '''
    
    syntax = { }
    default = { }
    
    def __init__(self, cfg=None):
        '''Performs configuration dictionary overlaying.'''
        self.syntax = merge_cls_dicts(self, 'syntax') # all in hierarchy
        self.cfg = ConfigDict(merge_cls_dicts(self, 'default'))
        if cfg:
            self.cfg.overlay(cfg) # apply user variables
        cfg_validate(self.cfg, self.syntax, type(self).__name__, warnings=False)
    
    
    _required_methods = [
        'on_yield',
        'on_notify', 'notify',
        'on_pre_reset', 'on_post_reset',
        'on_pre_breed', 'on_post_breed',
        'on_run_start', 'on_run_end',
        'on_exception',
        'should_terminate'
    ]
    
    @classmethod
    def isinstance(cls, inst):
        '''Returns ``True`` if `inst` is compatible with `MonitorBase`.
        
        An object is considered compatible if it is a subclass of
        `MonitorBase`, or if it implements the same methods. Methods are
        not tested for signatures, which may result in errors occurring
        later in the program.
        '''
        if isinstance(inst, cls): return True
        if inst is None: return False
        return all(hasattr(inst, method) for method in cls._required_methods)
    
    def on_yield(self, sender, name, group):
        '''Called for each population YIELDed in the system.
        
        If this function raises an exception, it will be passed to
        `on_exception`, `on_post_breed` will be called and if
        `should_terminate` returns ``False`` execution will continue
        normally.
        
        :Parameters:
          sender : `esec.system.System`
            The system instance reporting to this monitor.
        '''
        pass
    
    def on_notify(self, sender, name, value):
        '''Called in response to notifications from other objects. For
        example, a mutation operation may call ``notify`` to report to
        the monitor how many individuals were mutated. The monitor
        receives this message through `on_notify` and either ignores it
        or retains the statistic.
        
        If this function raises an exception, it will be passed to
        `on_exception`, `on_post_breed` will be called and if
        `should_terminate` returns ``False`` execution will continue
        normally.
        
        :Parameters:
          sender
            The sender of the notification message as provided by the
            call to ``notify``.
          
          name : string
            The name of the notification message as provided by the call
            to ``notify``.
          
          value
            The value of the notification message as provided by the
            call to ``notify``.
        '''
        pass
    
    def _on_notify(self, sender, name, value):
        '''Handles notification messages.
        
        :Parameters:
          sender
            The sender of the notification message as provided by the
            call to ``notify``.
          
          name : string
            The name of the notification message as provided by the call
            to ``notify``.
          
          value
            The value of the notification message as provided by the
            call to ``notify``.
        
        :Warn:
            Do not override this method to handle messages.
            That is what `on_notify` is for. Only override this
            method if you are implementing a queuing or
            synchronisation mechanism.
        '''
        self.on_notify(sender, name, value)
    
    def notify(self, sender, name, value):
        '''Sends a notification message to this monitor. This is used in
        contexts where a reference to the monitor is readily available.
        If the global ``notify`` function is available (for example, in
        selectors, generators or evaluators) it should be used instead.
        
        The global ``notify`` function can be obtained by importing
        `esec.context.notify`.
        
        :Parameters:
          sender
            The sender of the notification message as provided by the
            call to ``notify``.
          
          name : string
            The name of the notification message as provided by the
            call to ``notify``.
          
          value
            The value of the notification message as provided by the
            call to ``notify``.
        '''
        self._on_notify(sender, name, value)
    
    def on_pre_reset(self, sender):
        '''Called when the groups are reset, generally immediately after
        `on_run_start` is called.
        
        If this function or the system reset raises an exception, it
        will be passed to `on_exception`, `on_run_end` will be called
        and the run will be terminated.
        
        :Parameters:
          sender : `esec.system.System`
            The system instance reporting to this monitor.
        '''
        pass
    
    def on_post_reset(self, sender):
        '''Called immediately after the initialisation code specified in
        the system definition has executed.
        
        If this function or the system reset raises an exception, it
        will be passed to `on_exception`, `on_run_end` will be called
        and the run will be terminated.
        
        :Parameters:
          sender : `esec.system.System`
            The system instance reporting to this monitor.
        '''
        pass
    
    def on_pre_breed(self, sender):
        '''Called before breeding the current generation.
        
        If this function or the system breed raises an exception, it
        will be passed to `on_exception`, `on_post_breed` will be called
        and if `should_terminate` returns ``False`` execution will
        continue normally.
        
        :Parameters:
          sender : `esec.system.System`
            The system instance reporting to this monitor.
        '''
        pass
    
    def on_post_breed(self, sender):
        '''Called after breeding the current generation.
        
        If this function raises an exception, it will be handled by the
        Python interpreter.
        
        :Parameters:
          sender : `esec.system.System`
            The system instance reporting to this monitor.
        '''
        pass
    
    def on_run_start(self, sender):
        '''Called at the beginning of a run, before `on_pre_reset`.
        
        If this function raises an exception, it will be passed to
        `on_exception`, `on_run_end` will be called and the run will be
        terminated.
        
        :Parameters:
          sender : `esec.system.System`
            The system instance reporting to this monitor.
        '''
        pass
    
    def on_run_end(self, sender):
        '''Called at the end of a run, regardless of the reason for
        ending.
        
        If this function raises an exception, it will be handled by the
        Python interpreter.
        
        :Parameters:
          sender : `esec.system.System`
            The system instance reporting to this monitor.
        '''
        pass
    
    def on_exception(self, sender, exception_type, value, trace):
        '''Called when an exception is thrown.
        
        If this function raises an exception, it will be handled by the
        Python interpreter.
        
        :Parameters:
          sender : `esec.system.System`
            The system instance reporting to this monitor.
          
          exception_type : type(Exception)
            The type object representing the exception that was raised.
          
          value : Exception object
            The exception object that was raised.
          
          trace : string
            A displayable exception message formatted using the
            ``traceback`` module.
        '''
        pass
    
    def should_terminate(self, sender):     #pylint: disable=R0201,W0613
        '''Called after each experiment step to determine whether to
        terminate.
        
        :Parameters:
          sender : `esec.system.System`
            The system instance reporting to this monitor.
        
        :Returns:
            ``True`` if the run should terminate immediately; otherwise,
            ``False``.
        '''
        return True
    

from esec.monitors.consolemonitor import ConsoleMonitor
from esec.monitors.csvmonitor import CSVMonitor
from esec.monitors.multimonitor import MultiMonitor
from esec.monitors.multitarget import MultiTarget
from esec.monitors.posttarget import PostTarget

