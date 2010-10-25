'''A monitor that outputs to the console or other 'file-like' object
based on prespecified report strings in a CSV format.

See `esec.monitors` for a general overview of monitors.
'''
from esec.fitness import Fitness
from esec.monitors.consolemonitor import ConsoleMonitor
from esec.utils import ConfigDict

class CSVMonitor(ConsoleMonitor):
    '''A monitor that displays output using the console or other 'file-like' object
    based on prespecified report strings formatted for writing to a CSV file.
    
    See `esec.monitors` for a general overview of monitors.
    '''
    format = {
        # <name> : ['<header string>', '<format string>', '<self.call string>']
        # building blocks
        'gen':      [ 'Generation', '%d', 'stats.generations' ],
        'births':   [ 'Births', '%d', 'stats.births' ],
        'evals':    [ 'Evals', '%d', 'stats.global_evals' ],
        'local_evals':  [ 'Local evals', '%d', 'stats.local_evals' ],
        'stable_count': [ 'Stable', '%d', 'stats.stable_count' ],
        
        # These headers are merged into the titles
        'brief_header':  None,
        'best_header':   None,
        'global_header': None,
        'local_header':  None,
        'repro_header':  None,
        
        'best_bday':        [ 'Best Birthday', '%d', 'stats.global_max.birthday' ],
        'best_fit_int':     [ 'Best Fitness', '%d',   'stats.global_max.fitness.simple' ],
        'best_fit_float':   [ 'Best Fitness', '%f', 'stats.global_max.fitness.simple' ],
        'best_fit':         [ 'Best Fitness', '%s', 'stats.global_max.fitness' ],
        'best_genome':      [ 'Best Genome', '"%s"', 'stats.global_max.genome_string' ],
        'best_phenome':     [ 'Best Phenome', '"%s"', 'stats.global_max.phenome_string' ],
        'best_length':      [ 'Best Length', '%s', 'stats.global_max.length_string' ],
        
        'global_min_int':   [ 'Global Min. Fitness', '%d', 'stats.global_min.fitness.simple' ],
        'global_ave_int':   [ 'Global Mean Fitness', '%d', 'stats.global_ave_fitness.simple' ],
        'global_max_int':   [ 'Global Max. Fitness', '%d', 'stats.global_max.fitness.simple' ],
        'global_min_float': [ 'Global Min. Fitness', '%f', 'stats.global_min.fitness.simple' ],
        'global_ave_float': [ 'Global Mean Fitness', '%f', 'stats.global_ave_fitness.simple' ],
        'global_max_float': [ 'Global Max. Fitness', '%f', 'stats.global_max.fitness.simple' ],
        'global_min':       [ 'Global Min. Fitness', '%s', 'stats.global_min.fitness' ],
        'global_ave':       [ 'Global Mean Fitness', '%s', 'stats.global_ave_fitness' ],
        'global_max':       [ 'Global Max. Fitness', '%s', 'stats.global_max.fitness' ],
        'global_mutated':   [ 'Global Mutated', '%d', 'stats.global_mutated' ],
        'global_recombine': [ 'Global Recombined', '%d', 'stats.global_recombined' ],
        'global_invalid':   [ 'Global Invalids', '%d', 'stats.global_invalid' ],
        'step_ave':         [ 'Ave. Step', '%f', '_step_ave' ],
        
        'local_min_int':    [ 'Local Min. Fitness', '%d', 'stats.local_min.fitness.simple' ],
        'local_ave_int':    [ 'Local Mean Fitness', '%d', 'stats.local_ave_fitness.simple' ],
        'local_max_int':    [ 'Local Max. Fitness', '%d', 'stats.local_max.fitness.simple' ],
        'local_min_float':  [ 'Local Min. Fitness', '%f', 'stats.local_min.fitness.simple' ],
        'local_ave_float':  [ 'Local Mean Fitness', '%f', 'stats.local_ave_fitness.simple' ],
        'local_max_float':  [ 'Local Max. Fitness', '%f', 'stats.local_max.fitness.simple' ],
        'local_min':        [ 'Local Min. Fitness', '%s', 'stats.local_min.fitness' ],
        'local_ave':        [ 'Local Mean Fitness', '%s', 'stats.local_ave_fitness' ],
        'local_max':        [ 'Local Max. Fitness', '%s', 'stats.local_max.fitness' ],
        'local_mutated':    [ 'Local Mutated', '%d', 'stats.local_mutated' ],
        'local_recombine':  [ 'Local Recombined', '%d', 'stats.local_recombined' ],
        'local_invalid':    [ 'Local Invalids', '%d', 'stats.local_invalid' ],
        'local_unique':     [ 'Local Unique', '%d', 'stats.local_unique' ],
        'local_diversity':  [ 'Local Diversity', '%f', 'stats.local_diversity'],
        'local_dispersion': [ 'Local Dispersion', '%f', 'stats.local_dispersion'],
        # for GE landscapes only
        'local_no_compile': [ 'Did not compile', '%d', 'stats.local_did_not_compile', 0 ],
        
        'local_best_genome':    [ 'Local Best Genome', '"%s"', 'stats.local_max.genome_string' ],
        'local_best_phenome':   [ 'Local Best Phenome', '"%s"', 'stats.local_max.phenome_string' ],
        'local_best_length':    [ 'Local Best Length', '%s', 'stats.local_max.length_string' ],
        
        'species': 'births+deaths+global_mutated+step_ave+global_invalid+evals',
        
        'sizes': [ 'Sizes', '"%s"', '_sizes_info'],
        
        # abbreviations (unchanged from ConsoleMonitor, but behave differently
        # because some parts are now set to None)
        'brief': 'gen+births+evals+best_fit+|',
        'brief_int': 'gen+births+evals+best_fit_int+|',
        'brief_float': 'gen+births+evals+best_fit_float+|',
        'global': 'global_header+global_min+global_ave+global_max+|',
        'global_int': 'global_header+global_min_int+global_ave_int+global_max_int+|',
        'global_float': 'global_header+global_min_float+global_ave_float+global_max_float+|',
        'local': 'local_header+local_min+local_ave+local_max+|',
        'local_int': 'local_header+local_min_int+local_ave_int+local_max_int+|',
        'local_float': 'local_header+local_min_float+local_ave_float+local_max_float+|',
        'best': 'best_bday+best_fit+|',
        'best_int': 'best_bday+best_fit_int+|',
        'best_float': 'best_bday+best_fit_float+|',
        # some 'standard' formats don't make any sense, so ignore them
        'nl': None, '.': None, '|': None, ' ': None, ':': None,
        # end code [batch results]
        'status':['End status', '%s', '_status'],
        # elapsed CPU time
        'time': ['Elapsed time (ms)', '%d', '_time'],
        'time_delta': [ 'Delta time (ms)', '%d', '_time_delta'],
        'time_precise': ['Elapsed time (us)', '%d', '_time_precise'],
        'time_delta_precise': [ 'Delta time (us)', '%d', '_time_delta_precise'],
        # most recently executed block
        'block': [ 'Block', '%s', '_last_block'],
    }
    '''The set of known column descriptors.
    
    Each descriptor is either a string or a list of three elements. Strings are
    interpreted as a list of other headers, allowing multiple columns to be specified
    under one name. For example, ``'best'`` is defined as ``'best_bday+best_fit+|'``;
    specifying ``'best'`` in a report string is equivalent to specifying
    ``'best_bday+best_fit+|'``.
    
    Descriptors mapping to a list of three elements include, in order, a heading,
    a format string and a method or statistic name. The headings are used to display
    the heading of a table. The method name is mapped to a callable object or function
    on `ConsoleMonitor`. Specifying ``'stats.'`` at the start of the method name
    interprets the next dotted-part of the name as a member of the statistics object
    kept by the monitor, and the remainder as a member of that.
    
    For example, the value ``'stats.global_max.fitness'`` retrieves the value of
    ``global_max``. The displayed value, however, is the ``fitness`` member of the
    retrieved value.
    
    The format string is any standard Python format string.
    '''
    
    syntax = {
        'csv_formats?' : dict
    }
    '''The expected format of the configuration dictionary passed to `__init__`.
    
    See `ConsoleMonitor.syntax` for other available settings.

    .. include:: epydoc_include.txt
    
    Members:
      csv_formats : (dictionary)
        A dictionary of extra formats to include with those in `format`. These
        completely replace any settings provided in ``formats`` (from
        `ConsoleMonitor.syntax`).
    '''

    default = {
        'csv_formats': { },
    }

    def __init__(self, cfg):
        '''Initialises a new CSV monitor. Behaviour is similar to that
        of `ConsoleMonitor`, but output is formatted suitable for writing
        to a comma-separated-value format file.
        
        :Parameters:
          cfg : `ConfigDict`
            The set of parameters used to initialise this monitor.
            Parameter details can be found in at `syntax`.
        '''
        super(CSVMonitor, self).__init__(cfg)
        if False:
            # Satisfying pylint
            self.cfg.formats = None
    
    class _CallsWrapper(object):    #pylint: disable=R0903
        '''Intercepts the report format calls and converts strings to be
        safe for inclusion in a CSV file.
        '''
        def __init__(self, calls):
            self.calls = list(calls)
        
        def __iter__(self):
            for call in self.calls:
                yield lambda owner: self._make_csv_safe(call(owner))
        
        def _make_csv_safe(self, values):   #pylint: disable=R0201
            '''Returns a sequence of values taken from `values` with strings
            converted to be CSV-'safe'.
            
            :Note:
                `values` is typically a tuple but this method is a generator.
                For the current implementation of `ConsoleMonitor` this is
                fine, but if the implementation changes this may need to be
                updated.
            '''
            for value in values:
                if isinstance(value, Fitness):
                    yield value.comma_separated
                elif isinstance(value, str):
                    value = value.strip(' \n\r').replace('\n', '\\n').replace('\r', '\\r')
                    if r'\\' in value: value = '"' + value + '"'
                    yield value
                else:
                    yield value
    
    def parse_report(self, report): #pylint: disable=C0111
        self.cfg.formats = self.cfg.csv_formats
        hdrs, fmts, calls = self._parse_report(report)
        return (','.join(hdrs), ','.join(fmts), self._CallsWrapper(calls))
    
    def on_notify(self, sender, name, value):
        '''Handles various messages.'''
        if sender == 'Experiment':
            if name == 'Configuration':
                # `value` contains a ConfigDict
                assert isinstance(value, ConfigDict)
                # No verbose check when writing to external file
                print >> self.config_out, 'Configuration Information:'
                print >> self.config_out, '\n'.join(value.list())
                print >> self.config_out
                return
        elif sender == 'Monitor':
            if name == 'Statistics':
                # `value` contains the _stats dictionary
                print >> self.summary_out
                print >> self.summary_out, 'Statistic,Value'
                def _disp(source, scope):
                    '''Displays a dict/`ConfigDict` recursively with commas separating keys
                    and values.'''
                    for key, value in sorted(source.iteritems()):
                        if isinstance(value, (dict, ConfigDict)): _disp(value, scope + key + '.')
                        else: print >> self.summary_out, scope + key + ',' + ('%s' % value)
                _disp(value, '')
                return
        
        # Unhandled message
        super(CSVMonitor, self).on_notify(sender, name, value)
    
    # override time functions to return milliseconds/microseconds only
    def _time(self, owner):
        '''Returns ``(milliseconds,)`` that the process has been active for.'''
        return (self._get_ms(),)
    
    def _time_delta(self, owner):
        '''Returns ``(milliseconds,)`` since the last call to `_time_delta`.'''
        prev_time = self._last_time_ms
        now_time = self._last_time_ms = self._get_ms()
        return (now_time - prev_time,) if prev_time is not None else (0,)
    
    def _time_precise(self, owner):
        '''Returns ``(microseconds,)`` since the first call to `_time_precise`.'''
        return (self._get_us(),)
    
    def _time_delta_precise(self, owner):
        '''Returns ``(microseconds,)`` since the last call to `_time_delta_precise`.'''
        prev_time = self._last_time_us
        now_time = self._last_time_us = self._get_us()
        return (now_time - prev_time,) if prev_time is not None else (0,)
