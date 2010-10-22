'''A monitor that displays output using the console or other 'file-like' object
based on prespecified report strings.

See `esec.monitors` for a general overview of monitors.
'''
from esec.individual import EmptyIndividual
from esec.fitness import Fitness, EmptyFitness
from esec.monitors import MonitorBase
from esec.utils import ConfigDict, is_ironpython

import sys
import os, os.path
if os.name == 'nt':
    from ctypes import windll, c_ulonglong, c_void_p, byref
from time import clock

class NullStream(object):
    '''A stream target that drops all writes.'''
    def write(self, value):
        '''Ignores the provided value.'''
        pass
    
    def flush(self):
        '''Does nothing.'''
        pass

class ConsoleMonitor(MonitorBase):  #pylint: disable=R0902
    '''A monitor that displays output using the console or other 'file-like' object
    based on prespecified report strings.
    
    See `esec.monitors` for a general overview of monitors.
    '''
    format = {
        # <name> : ['<header string>', '<format string>', '<self.call string>']
        # building blocks
        'gen':      [ ' #gen.  ', '%7d ', 'stats.generations' ],
        'births':   [ ' births ', '%7d ', 'stats.births' ],
        'evals':    [ ' evals  ', '%7d ', 'stats.global_evals' ],
        'local_evals':  [ ' evals  ', '%7d ', 'stats.local_evals' ],
        'stable_count': [ ' stable ', '%7d ', 'stats.stable_count' ],
        
        'brief_header':     [ ' Brief:  ', '         ', None ],
        'best_header':      [ ' Best:   ', '         ', None ],
        'global_header':    [ ' Global: ', '         ', None ],
        'local_header':     [ ' Local:  ', '         ', None ],
        'repro_header':     [ ' Repro:  ', '         ', None ],
        
        'best_bday':        [ ' b-date   ', ' %9d ', 'stats.global_max.birthday' ],
        'best_fit_int':     [ '  fitness        ', '%16d ',   'stats.global_max.fitness.simple' ],
        'best_fit_float':   [ '  fitness        ', '%16.3e ', 'stats.global_max.fitness.simple' ],
        'best_fit':         [ '  fitness        ', '%16s ', 'stats.global_max.fitness' ],
        'best_genome':      [ ' genome ', ' %s', 'stats.global_max.genome_string' ],
        'best_phenome':     [ ' phenome ', ' %s', 'stats.global_max.phenome_string' ],
        'best_length':      [ ' length ', '%7s ', 'stats.global_max.length_string' ],
        
        'global_min_int':   [ '  minimum     ', '%13d ', 'stats.global_min.fitness.simple' ],
        'global_ave_int':   [ '  average     ', '%13d ', 'stats.global_ave_fitness.simple' ],
        'global_max_int':   [ '  maximum     ', '%13d ', 'stats.global_max.fitness.simple' ],
        'global_min_float': [ '  minimum     ', '%13.5e ', 'stats.global_min.fitness.simple' ],
        'global_ave_float': [ '  average     ', '%13.5e ', 'stats.global_ave_fitness.simple' ],
        'global_max_float': [ '  maximum     ', '%13.5e ', 'stats.global_max.fitness.simple' ],
        'global_min':       [ '  minimum        ', '%16s ', 'stats.global_min.fitness' ],
        'global_ave':       [ '  average        ', '%16s ', 'stats.global_ave_fitness' ],
        'global_max':       [ '  maximum        ', '%16s ', 'stats.global_max.fitness' ],
        'global_mutated':   [ ' mutation  ', '%10d ', 'stats.global_mutated' ],
        'global_recombine': [ ' recombine ', '%10d ', 'stats.global_recombined' ],
        'global_invalid':   [ ' violation ', '%10d ', 'stats.global_invalid' ],
        'step_ave':         [ ' ave.step ', '%9f ', '_step_ave' ],
        
        'local_min_int':    [ '  minimum     ', '%13d ', 'stats.local_min.fitness.simple' ],
        'local_ave_int':    [ '  average     ', '%13d ', 'stats.local_ave_fitness.simple' ],
        'local_max_int':    [ '  maximum     ', '%13d ', 'stats.local_max.fitness.simple' ],
        'local_min_float':  [ '  minimum     ', '%13.5e ', 'stats.local_min.fitness.simple' ],
        'local_ave_float':  [ '  average     ', '%13.5e ', 'stats.local_ave_fitness.simple' ],
        'local_max_float':  [ '  maximum     ', '%13.5e ', 'stats.local_max.fitness.simple' ],
        'local_min':        [ '  minimum        ', '%16s ', 'stats.local_min.fitness' ],
        'local_ave':        [ '  average        ', '%16s ', 'stats.local_ave_fitness' ],
        'local_max':        [ '  maximum        ', '%16s ', 'stats.local_max.fitness' ],
        'local_mutated':    [ ' mutation  ', '%10d ', 'stats.local_mutated' ],
        'local_recombine':  [ ' recombine ', '%10d ', 'stats.local_recombined' ],
        'local_invalid':    [ ' violation ', '%10d ', 'stats.local_invalid' ],
        'local_unique':     [ ' unique    ', '%10d ', 'stats.local_unique' ],
        'local_diversity':  [ ' diversity  ', '%11g ', 'stats.local_diversity'],
        'local_dispersion': [ ' dispersion ', '%11g ', 'stats.local_dispersion'],
        # for GE landscapes only
        'local_no_compile': [ ' !compile ', '%9d ', 'stats.local_did_not_compile', 0 ],
        
        'local_best_genome':    [ ' genome ', ' %s', 'stats.local_max.genome_string' ],
        'local_best_phenome':   [ ' phenome ', ' %s', 'stats.local_max.phenome_string' ],
        'local_best_length':    [ ' length ', '%7s ', 'stats.local_max.length_string' ],
        
        'species': 'births+deaths+global_mutated+step_ave+global_invalid+evals',
        
        'sizes': [ '    sizes     ', ' %-12s ', '_sizes_info'],
        
        # abbreviations
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
        # multi-liners
        # if you want a new-line, why not...
        'nl':    ['', '\n', None],
        # column separators
        '.': ['', '.', None],
        '|': [ '|', '|', None ],
        ' ': [ ' ', ' ', None ],
        ':': [ ':', ':', None ],
        # end code [batch results]
        'status':[' end status ', '%12s', '_status'],
        # elapsed CPU time
        'time': [' elapsed time  ', "%4d:%02d'%02d.%03d ", '_time'],
        'time_delta': [ ' delta time    ', "%4d:%02d'%02d.%03d ", '_time_delta'],
        'time_precise': [' elapsed time      ', "%4d:%02d'%02d.%03d.%03d ", '_time_precise'],
        'time_delta_precise': [ ' delta time        ', "%4d:%02d'%02d.%03d.%03d ", '_time_delta_precise'],
        # most recently executed block
        'block': [ '  block           ', ' %-16s ', '_last_block'],
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
    
    if len('%10.1e' % 1.0) != 10:
        # IronPython handles the %e format badly, so detect this and work around it.
        # (Using a test instead of is_ironpython() in case it gets fixed.)
        format.update({
            'best_fit_float':   [ '  fitness        ', '%17.3e ', 'stats.global_max.fitness.simple' ],
            
            'global_min_float': [ '  minimum     ', '%14.5e ', 'stats.global_min.fitness.simple' ],
            'global_ave_float': [ '  average     ', '%14.5e ', 'stats.global_ave_fitness.simple' ],
            'global_max_float': [ '  maximum     ', '%14.5e ', 'stats.global_max.fitness.simple' ],
            
            'local_min_float':  [ '  minimum     ', '%14.5e ', 'stats.local_min.fitness.simple' ],
            'local_ave_float':  [ '  average     ', '%14.5e ', 'stats.local_ave_fitness.simple' ],
            'local_max_float':  [ '  maximum     ', '%14.5e ', 'stats.local_max.fitness.simple' ],
        })
    
    syntax = {
        'out?': '*',
        'report_out': '*',
        'summary_out': '*',
        'config_out': '*',
        'error_out': '*',
        'verbose': int,
        'primary': str,
        'report': str,
        'summary': str,
        'exception_summary': str,
        'limits?': {
            'generations?': [int, None],
            'stable?': [int, None],
            'fitness?': '*',
            'unique?': [int, None],
        },
        'formats?' : dict,
    }
    '''The expected format of the configuration dictionary passed to `__init__`.
    
    .. include:: epydoc_include.txt
    
    Members:
      verbose : (int |ge| 0 [defaults to zero])
        The verbosity level to use.
      
      out : (writeable [optional])
        The file-like object to write all details to. If specified,
        ``report_out``, ``summary_out`` and ``config_out`` are ignored.
      
      report_out : (writeable [defaults to ``sys.stdout``])
        The file-like object to write report details to.
      
      summary_out : (writeable [defaults to ``sys.stdout``])
        The file-like object to write report summaries to.
      
      config_out : (writeable [defaults to ``sys.stdout``])
        The file-like object to write configuration details to.
      
      error_out : (writeable [defaults to ``sys.stderr``])
        The file-like object to write error details to.
      
      primary : (str [defaults to ``'population'``])
        The name of the primary population. The primary population is used
        to determine whether termination conditions have been reached.
      
      report : (str [defaults to ``'brief+global'``])
        The report format string, made up of the desired report column
        names (from `format`) concatenated with '+' symbols.
      
      summary : (str [defaults to ``'status+best+best_phenome'``])
        The summary format string, made up of the desired report column
        names (from `format`) concatenated with '+' symbols.
      
      exception_summary : (str [defaults to ``'status+gen+births+evals'``])
        The summary format string to use when an exception has terminated
        the experiment. Uses the same syntax as ``summary``. (Override
        the `on_exception` function to provide different handling of
        exceptions.)
      
      limits.generations : (int > 0 [optional])
        Terminate after this number of generations have been executed.
      
      limits.stable : (int > 0 [optional])
        Terminate after this many generations without an improvement in
        the best individual.
      
      limits.fitness : (`Fitness` [optional])
        Terminate when the best individual has a fitness better than
        this.
      
      limits.unique : (int |ge| 1 [optional])
        Terminate when the number of unique individuals (based on
        phenome) in the primary population reaches or falls below
        this.
      
      formats : (dictionary)
        A dictionary of extra formats to include with those in `format`.
    '''
    
    default = {
        'report_out': sys.stdout,
        'summary_out': sys.stdout,
        'config_out': sys.stdout,
        'error_out': sys.stderr,
        'verbose': 0,
        'primary': 'population',
        'report': 'brief+global',
        'summary': 'status+best+best_phenome',
        'exception_summary': 'status+gen+births+evals',
        'formats': { },
        'limits': { }
    }
    
    def __init__(self, cfg):
        '''Initialises a new console monitor.
        
        :Parameters:
          cfg : `ConfigDict`
            The set of parameters used to initialise this monitor.
            Parameter details can be found in at `syntax`.
        '''
        super(ConsoleMonitor, self).__init__(cfg)
        
        self.verbose = self.cfg.verbose
        
        # ------------------------------------------------------------
        # Load the output files/streams
        
        #  - Read from config
        self.report_out = self.cfg.report_out
        self.summary_out = self.cfg.summary_out
        self.config_out = self.cfg.config_out
        self.error_out = self.cfg.error_out
        
        # - Override with .out (if specified)
        if 'out' in self.cfg and self.cfg.out:
            self.report_out = self.cfg.out
            self.summary_out = self.cfg.out
            self.config_out = self.cfg.out
        
        # - Open filenames with optional overwrite-protection
        def _do_open(filename):
            '''Opens a file with the name or pattern provided. If `filename`
            contains a ``%`` symbol, it is formatted with a unique integer
            index.
            '''
            if '%' in filename:
                i = 0
                fname = filename % i
                while os.path.exists(fname):
                    i += 1
                    fname = filename % i
                return open(fname, 'w')
            else:
                return open(fname, 'a')
        
        # - Replace filenames with file objects without opening the
        #   same file multiple times
        opened_files = { }
        def _update_opened(filename):
            '''Updates ``opened_files``.'''
            if isinstance(filename, str):
                if filename not in opened_files:
                    opened_files[filename] = _do_open(filename)
        def _get_opened(filename):
            '''Gets the appropriate value from ``opened_files``.'''
            if isinstance(filename, str):
                return opened_files.get(filename, None)
            elif filename == None:
                return NullStream()
            else:
                return filename
        
        _update_opened(self.report_out)
        _update_opened(self.summary_out)
        _update_opened(self.config_out)
        _update_opened(self.error_out)
        self.report_out = _get_opened(self.report_out)
        self.summary_out = _get_opened(self.summary_out)
        self.config_out = _get_opened(self.config_out)
        self.error_out = _get_opened(self.error_out)
        
        # ------------------------------------------------------------
        # Load the limits
        
        self.limits = self.cfg.limits
        
        # - Ensure limits.fitness is a Fitness object
        if 'fitness' in self.limits:
            if not isinstance(self.limits.fitness, Fitness):
                self.limits.fitness = Fitness(self.limits.fitness)
        
        # - Delete any limits that are set to None
        if self.limits:
            none_limits = [k for k in self.limits if self.limits[k] == None]
            for k in none_limits: del self.limits[k]
        
        self.primary = self.cfg.primary
        
        self.report = self.parse_report(self.cfg.report)
        self.summary = self.parse_report(self.cfg.summary)
        self.exception_summary = self.parse_report(self.cfg.exception_summary)
        
        # These statistics are slow to calculate, so only bother if we're interested in them
        part_list = set(self.cfg.report.split('+') + \
                        self.cfg.summary.split('+') + \
                        self.cfg.exception_summary.split('+'))
        self.measure_diversity = 'local_diversity' in part_list
        '''``True`` if diversity should be calculated for each group; otherwise, ``False``.'''
        self.measure_dispersion = 'local_dispersion' in part_list
        '''``True`` if dispersion should be calculated for each group; otherwise, ``False``.'''
        self.measure_unique = 'local_unique' in part_list or 'unique' in self.limits
        '''``True`` if the number of unique individuals should be calculated for each group; otherwise, ``False``.'''
        
        # ------------------------------------------------------------
        # Other members
        self._start_time_ms = 0L
        self._start_time_ms = self._get_ms()
        self._last_time_ms = None
        self._start_time_us = 0L
        self._start_time_us = self._get_us()
        self._last_time_us = None
        self.stop_now = False
        self.end_code = None
        self._stats = None
        self._last_block_name = 'initialisation'
    
    class _read_stats(object):  #pylint: disable=C0103,R0903
        '''Read any specified statistic from the primary population's Statistics object
        
        If a value for ``member`` is provided, the value of that member is returned.
        
        If the value is a tuple it is returned unmodified. Otherwise, a single element
        tuple is returned containing the value read.'''
        
        def __init__(self, key, member=None, default=None):
            '''Initialises a new instance of `_read_stats`.
            
            :Parameters:
              key : string
                The key to look up in ``owner._stats``.
              
              member : string [optional]
                The member to look up in the returned statistic. This may contain
                multiple parts, separated by period characters.
              
              default : [optional]
                The value to return if `key` or `member` are not found. If ``None``
                or omitted, an assertion is raised when a value is not found.
            '''
            self.key = key
            self.member = member.split('.') if member else None
            self.default = default
        
        def __call__(self, owner):
            value = owner._stats.get(self.key)     #pylint: disable=W0212
            if value != None and self.member:
                for part in self.member:
                    if hasattr(value, '__getitem__'):
                        try:
                            value = value[part]
                        except (KeyError, IndexError, TypeError):
                            value = getattr(value, part, self.default)
                        except:
                            value = self.default
                    else:
                        value = getattr(value, part, self.default)
                    assert value != None, 'Statistic ' + self.key + ' has no member ' + '.'.join(self.member) + '.'
            if value == None and self.default != None:
                value = self.default
            if isinstance(value, tuple):
                return value
            else:
                return (value,)
    
    def parse_report(self, report):
        '''Parses the report string provided in `report`.
        
        :Returns:
            A tuple containing the header string, the format string and a
            list of function calls to obtain the values for the format
            string.
        
        :Exceptions:
          - `ValueError` : A name in `report` is not recognised.
        '''
        hdrs, fmts, calls = self._parse_report(report)
        return (''.join(hdrs), ''.join(fmts), calls)
    
    def _parse_report(self, report):
        '''Does the actual parsing promised by `parse_report`.
        '''
        def make_call(call, default):
            '''Converts a string into a method reference.'''
            if call == None: return self._noop
            if hasattr(call, '__call__'): return call
            
            bit, _, stat = call.partition('.')
            if bit == 'stats' and stat:
                stat, _, memb = stat.partition('.')
                return self._read_stats(stat, memb, default)
            
            result = self
            for bit in call.split('.'):
                result = getattr(result, bit)
            return result
        
        hdrs, fmts, calls = [], [], []
        for cmd in (s.strip() for s in report.split('+')):
            value = self.cfg.formats.get(cmd) or self.format.get(cmd)
            if isinstance(value, str):
                hdr, fmt, call = self._parse_report(value)
                hdrs.extend(hdr)
                fmts.extend(fmt)
                calls.extend(call)
            elif value:
                if len(value) == 4:
                    hdr, fmt, target, default = value
                else:
                    hdr, fmt, target = value
                    default = None
                hdrs.append(hdr)
                fmts.append(fmt)
                calls.append(make_call(target, default))
            else:
                # Double-check that it wasn't there with a value of None
                if cmd not in self.format and cmd not in self.cfg.formats:
                    raise ValueError(cmd + " is not a known 'report' type.")
        
        return (hdrs, fmts, calls)
    
    def on_yield(self, sender, name, group):
        '''Collates individual statistics for each
        group. Statistics for the primary population are promoted
        to the main statistics dictionary to be accessible for
        the report.
        '''
        self._stats['groups'].update([name])
        self._stats[name] = pop_stat = self._stats.get(name, { })
        
        best = EmptyIndividual()
        worst = group[0] if len(group) else EmptyIndividual()
        fit_sum = EmptyFitness()
        for i in group:
            # Accumulate fitness before statistics because i.fitness
            # may increment the 'evals' statistic.
            fit_sum += i.fitness
            if i.fitness > best.fitness: best = i
            if i.fitness < worst.fitness: worst = i
            
            items = i.statistic.items()
            for key, value in items:
                for prefix in ('global_', 'local_'):
                    fullkey = prefix + key
                    if fullkey in pop_stat: pop_stat[fullkey] += value
                    else: pop_stat[fullkey] = value
        
        # Update local stats
        pop_stat['local_max'] = best
        pop_stat['local_ave_fitness'] = fit_sum / float(len(group))
        pop_stat['local_min'] = worst
        
        # Update global stats
        pop_max = pop_stat.get('global_max', EmptyIndividual())
        if best.fitness > pop_max.fitness:
            pop_max = best
            pop_stat['stable_count'] = 0
        else:
            pop_stat['stable_count'] = pop_stat.get('stable_count', 0) + 1
        pop_min = pop_stat.get('global_min', worst)
        if worst.fitness < pop_min.fitness:
            pop_min = worst
        pop_sum = pop_stat.get('_global_sum_fitness', EmptyFitness()) + fit_sum
        pop_cnt = pop_stat.get('_global_cnt_fitness', 0) + float(len(group))
        pop_stat['global_max'] = pop_max
        pop_stat['_global_sum_fitness'] = pop_sum
        pop_stat['_global_cnt_fitness'] = pop_cnt
        pop_stat['global_ave_fitness'] = pop_sum / pop_cnt
        pop_stat['global_min'] = pop_min
        
        pop_stat['local_diversity'] = 0.0
        pop_stat['local_dispersion'] = 0.0
        pop_stat['local_unique'] = 0.0
        ## TODO: Implement diversity and dispersion measures
        if self.measure_diversity:
            pass
        if self.measure_dispersion:
            pass
        if self.measure_unique:
            pop_stat['local_unique'] = len(set([g.phenome_string for g in group]))
        
        # Update size
        pop_stat['size'] = len(group)
        
        if name == self.primary:
            # If this is the primary, transfer all stats out to the
            # root object.
            self._stats.update(pop_stat)
    
    
    def on_notify(self, sender, name, value):   #pylint: disable=R0912,R0915
        '''Handles various messages.'''
        if sender == 'Experiment':
            if name == 'System':
                # `value` contains a System
                print >> self.config_out, 'System Information:'
                print >> self.config_out, '\n'.join(value.info(level=self.verbose))
                print >> self.config_out
                self.config_out.flush()
            elif name == 'Landscape':
                # `value` contains a Landscape
                print >> self.config_out, 'Landscape Infomation:'
                print >> self.config_out, '  ' + '\n  '.join(value.info(level=self.verbose))
                print >> self.config_out
                self.config_out.flush()
            elif name == 'Configuration':
                # `value` contains a ConfigDict
                assert isinstance(value, ConfigDict)
                if self.verbose > 3:
                    print >> self.config_out, 'Configuration Information:'
                    print >> self.config_out, '\n'.join(value.list())
                    print >> self.config_out
                self.config_out.flush()
        
        elif sender == 'System':
            if name == 'Block':
                # `value` contains a block name
                key = value
                self._last_block_name = key
                blocks = self._stats['blocks']
                if key in blocks:
                    blocks[key] += 1
                else:
                    blocks[key] = 1
        
        elif sender == 'Monitor':
            if name == 'Statistics':
                # `value` contains the _stats dictionary
                print >> self.summary_out
                if not value: value = self._stats
                print >> self.summary_out, '\n'.join(sorted(ConfigDict(value).lines()))
        
        elif name == 'statistic':
            # `value` contains a string or dictionary of statistics to increment
            if isinstance(value, str):
                value = dict(((k, 1) for k in value.split('+')))
            
            assert isinstance(value, dict), "Value for 'statistic' must be a dict or str"
            
            for key, value in value.iteritems():
                if key in self._stats:
                    self._stats[key] += value
                else:
                    self._stats[key] = value
        
        elif name == 'aborted':
            # keep mutate_insert/crossover type messages quiet, but count them
            for key in ('global_%s_aborted' % sender, 'local_%s_aborted' % sender):
                self._stats[key] = self._stats.get(key, 0) + 1

        elif name == 'message':
            # `value` contains a string or list of strings to display to the user
            if isinstance(value, (tuple, list)): value = '\n'.join(value)
            assert isinstance(value, str)
            print >> self.error_out, value
        
        else:
            if self.verbose > 1:
                print >> self.error_out, name, 'from', sender
                print >> self.error_out, value
    
    def on_pre_reset(self, sender):
        '''Resets the generation count, best individual and average
        fitness.
        '''
        self._stats = {
            'generations': 0,
            'births': 0,
            'stable_count': 0,
            'global_evals': 0,
            'local_evals': 0,
            'groups': set(),
            'blocks': { },
            self.primary : { 'global_max': EmptyIndividual() }
        }
        self.stop_now = False
        self.end_code = None
    
    def on_post_reset(self, sender):
        '''Displays the state of the initial population.'''
        rep = self.report
        if rep and not self.stop_now and self._stats['groups']:
            values = []
            for value_list in [call(self) for call in rep[2]]:
                values.extend(value_list)
            try:
                print >> self.report_out, rep[1] % tuple(values)
            except TypeError:
                # normally thrown because of invalid values
                print >> self.error_out, 'Format string:', rep[1]
                print >> self.error_out, 'Values:       ', values
                raise
    
    
    def on_pre_breed(self, sender):
        '''Increments the breed count and resets local statistics.'''
        self._stats['generations'] += 1
        self._stats['stable_count'] += 1
        
        local_stats = [k for k in self._stats if k.startswith('local_')]
        for key in local_stats:
            del self._stats[key]
        
        for group in self._stats['groups']:
            local_stats = [k for k in self._stats[group] if k.startswith('local_')]
            for key in local_stats:
                del self._stats[group][key]
    
    
    def on_post_breed(self, sender):
        '''Displays the report values and resets individual's statistics.'''
        if self.stop_now: return
        
        rep = self.report
        if rep:
            values = []
            for value_list in [call(self) for call in rep[2]]:
                values.extend(value_list)
            try:
                print >> self.report_out, rep[1] % tuple(values)
            except TypeError:
                # normally thrown because of invalid values
                print >> self.error_out, 'Format string:', rep[1]
                print >> self.error_out, 'Values:       ', values
                raise
    
    def on_run_start(self, sender):
        '''Displays the headings for the report.'''
        
        rep = self.report
        if rep:
            print >> self.report_out, rep[0]
    
    def on_run_end(self, sender):
        '''Displays the summary report. If verbosity is
        set to 4 or higher, displays the full set of statistics.
        '''
        rep = self.exception_summary if self.stop_now else self.summary
        
        if rep:
            print >> self.summary_out, rep[0]
            values = []
            for value_list in [call(self) for call in rep[2]]:
                values.extend(value_list)
            try:
                print >> self.summary_out, rep[1] % tuple(values)
            except TypeError:
                # normally thrown because of invalid values
                print >> self.error_out, 'Format string:', rep[1]
                print >> self.error_out, 'Values:       ', values
                raise
            
            if self.verbose >= 2:
                self.notify('Monitor', 'Statistics', self._stats)
        
        self.report_out.flush()
        self.summary_out.flush()
    
    
    def on_exception(self, sender, exception_type, value, trace):
        '''Displays the exception trace and terminates immediately.'''
        try:
            print >> self.error_out, '\n' + trace
        except (ValueError, IOError):
            print "IOError writing to output file. Writing exception to stdout."
            print trace
        self.stop_now = True
        self.end_code = 'EXCEPTION'
    
    def should_terminate(self, sender):
        '''Returns ``True`` if an exception has occurred or
        one of the generation or fitness limits have been reached.
        '''
        if self.end_code: return True
        
        if self.stop_now:
            self.end_code = 'EXCEPTION'
        elif 'generations' in self.limits and 'generations' in self._stats and \
             self._stats['generations'] >= self.limits.generations:
            self.end_code = 'GEN_LIMIT'
        elif 'fitness' in self.limits and 'global_max' in self._stats and \
             self._stats['global_max'].fitness >= self.limits.fitness:
            self.end_code = 'FIT_LIMIT'
        elif 'stable' in self.limits and 'stable_count' in self._stats and \
             self._stats['stable_count'] >= self.limits.stable:
            self.end_code = 'STABLE_LIMIT'
        elif 'unique' in self.limits and 'local_unique' in self._stats and \
             self._stats['local_unique'] <= self.limits.unique:
            self.end_code = 'UNIQUE_LIMIT'
        
        return bool(self.end_code)
    
    
    # Report functions
    
    # Disable method could be a function, unused parameter
    #pylint: disable=R0201, W0613
    
    def _noop(self, owner):
        '''Return nothing (but an empty tuple) '''
        return ()
    
    def _sizes_info(self, owner):
        '''Return the last size of every known group.'''
        _stats = self._stats
        return (','.join(('%s: %d' % (g, _stats[g]['size']) for g in _stats['groups'])),)
    
    def _status(self, owner):
        '''Return the end code.
        '''
        return (self.end_code or '-',)
    
    # define a platform specific _get_ms() function, used by _time() below
    if os.name == 'nt':
        if not is_ironpython():
            windll.kernel32.GetProcessTimes.argtypes = [ c_void_p ] * 5
        def _get_ms(self):
            '''Returns the number of milliseconds the process has been active for.
            '''
            createTime, exitTime, kernelTime, userTime = c_ulonglong(), c_ulonglong(), c_ulonglong(), c_ulonglong()
            if windll.kernel32.GetProcessTimes(-1,                  # current process
                                               byref(createTime),   # process start time (ignored)
                                               byref(exitTime),     # process end time (ignored)
                                               byref(kernelTime),   # time spent in kernel mode
                                               byref(userTime)):    # time spent in user mode
                now_time = (kernelTime.value + userTime.value) // 10000L
                return now_time - self._start_time_ms
            else:
                # GetProcessTimes call failed for some reason, so fall back on clock().
                # We assume that one failure means it fails all the time, so the values
                # returned won't be inconsistent.
                return long(clock() * 1000.0) - self._start_time_ms
        
    else:
        def _get_ms(self):
            '''Returns the number of milliseconds the process has been active for.
            '''
            return long(clock() * 1000.0) - self._start_time_ms
    
    def _get_us(self):
        '''Returns the number of microseconds since the first call.
        '''
        return long(clock() * 1000000.0) - self._start_time_us
    
    def _time(self, owner):
        '''Returns ``(hours, minutes, seconds, milliseconds)`` since the first call
        to `_time`.
        '''
        milliseconds = self._get_ms()
        seconds = milliseconds // 1000
        minutes = seconds // 60
        hours = minutes // 60
        milliseconds -= seconds * 1000
        seconds -= minutes * 60
        minutes -= hours * 60
        return (hours, minutes, seconds, milliseconds)
    
    def _time_delta(self, owner):
        '''Returns ``(hours, minutes, seconds, milliseconds)`` since the last call to
        `_time_delta`.
        '''
        prev_time = self._last_time_ms
        now_time = self._last_time_ms = self._get_ms()
        if prev_time == None:
            return (0, 0, 0, 0)
        else:
            milliseconds = now_time - prev_time
            seconds = milliseconds // 1000
            minutes = seconds // 60
            hours = minutes // 60
            milliseconds -= seconds * 1000
            seconds -= minutes * 60
            minutes -= hours * 60
            return (hours, minutes, seconds, milliseconds)

    def _time_precise(self, owner):
        '''Returns ``(hours, minutes, seconds, milliseconds, microseconds)`` since the
        first call to `_time_precise`.
        '''
        microseconds = self._get_us()
        milliseconds = microseconds // 1000
        seconds = milliseconds // 1000
        minutes = seconds // 60
        hours = minutes // 60
        microseconds -= milliseconds * 1000
        milliseconds -= seconds * 1000
        seconds -= minutes * 60
        minutes -= hours * 60
        return (hours, minutes, seconds, milliseconds, microseconds)
    
    def _time_delta_precise(self, owner):
        '''Returns ``(hours, minutes, seconds, milliseconds, microseconds)`` since the
        last call to `_time_delta_precise`.
        '''
        prev_time = self._last_time_us
        now_time = self._last_time_us = self._get_us()
        if prev_time == None:
            return (0, 0, 0, 0, 0)
        else:
            microseconds = now_time - prev_time
            milliseconds = microseconds // 1000
            seconds = milliseconds // 1000
            minutes = seconds // 60
            hours = minutes // 60
            microseconds -= milliseconds * 1000
            milliseconds -= seconds * 1000
            seconds -= minutes * 60
            minutes -= hours * 60
            return (hours, minutes, seconds, milliseconds, microseconds)
    
    def _last_block(self, owner):
        '''Returns ``(last_block_name,)``.'''
        return (self._last_block_name,)
