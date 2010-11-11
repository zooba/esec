'''A monitor that contains multiple monitors, allowing different types
of monitors to be used in the same experiment.

See `esec.monitors` for a general overview of monitors.
'''
from esec.monitors import MonitorBase

class MultiMonitor(MonitorBase):  #pylint: disable=R0902
    '''A monitor that redirects all callbacks to a set of child
    monitors.
    
    See `esec.monitors` for a general overview of monitors.
    '''
    
    syntax = {
        'monitors?' : list,
    }
    '''The expected format of the configuration dictionary passed to
    `__init__`.
    
    Members:
      monitors : (list of `MonitorBase` objects)
        The monitors to direct all callbacks to.
    '''
    
    def __init__(self, cfg):
        '''Initialises a new console monitor.
        
        :Parameters:
          cfg : `ConfigDict`
            The set of parameters used to initialise this monitor.
            Parameter details can be found in at `syntax`.
        '''
        super(MultiMonitor, self).__init__(cfg)
        
        self._monitors = self.cfg.monitors
        assert all(isinstance(i, MonitorBase) for i in self._monitors)
    
    
    def on_yield(self, sender, name, group):
        '''Redirects the yielded groups to all monitors in the order
        they were provided.
        '''
        for monitor in self._monitors:
            monitor.on_yield(sender, name, group)
    
    def on_notify(self, sender, name, value):
        '''Redirects the notification message to all monitors in the
        order they were provided.
        '''
        for monitor in self._monitors:
            monitor.on_notify(sender, name, value)
    
    def on_pre_reset(self, sender):
        '''Redirects the pre-reset callback to all monitors in the order
        they were provided.
        '''
        for monitor in self._monitors:
            monitor.on_pre_reset(sender)
    
    def on_post_reset(self, sender):
        '''Redirects the post-reset callback to all monitors in the
        order they were provided.
        '''
        for monitor in self._monitors:
            monitor.on_post_reset(sender)
    
    def on_pre_breed(self, sender):
        '''Redirects the pre-breed callback to all monitors in the order
        they were provided.
        '''
        for monitor in self._monitors:
            monitor.on_pre_breed(sender)
    
    def on_post_breed(self, sender):
        '''Redirects the post-reset callback to all monitors in the
        order they were provided.
        '''
        for monitor in self._monitors:
            monitor.on_post_breed(sender)
    
    def on_run_start(self, sender):
        '''Redirects the run start callback to all monitors in the order
        they were provided.
        '''
        for monitor in self._monitors:
            monitor.on_run_start(sender)
    
    def on_run_end(self, sender):
        '''Redirects the run end callback to all monitors in the order
        they were provided.
        '''
        for monitor in self._monitors:
            monitor.on_run_end(sender)
    
    def on_exception(self, sender, exception_type, value, trace):
        '''Redirects the exception callback to all monitors in the order
        they were provided.
        '''
        for monitor in self._monitors:
            monitor.on_exception(sender, exception_type, value, trace)
    
    def should_terminate(self, sender):
        '''Redirects the terminate query to all monitors in the order
        they were provided.
        
        Returns ``True`` if *any* monitor returns ``True``. All monitors
        will be queried.
        '''
        result = False
        for monitor in self._monitors:
            # Separate statement to ensure method is called
            partial_result = monitor.should_terminate(sender)
            result = result or partial_result
        return result
