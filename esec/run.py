'''.. title: ESEC Command-line Interface
.. include:: epydoc_include.txt

===========================
ESEC Command-line Interface
===========================

This script provides an efficient command line interface to run single or
multiple experiments using |esec|.

All configuration information can be provided using command line arguments,
however for research experiments the recommended method is to use a batch file
and store the results to file. This allows experiments to be easily reproduced
if necessary.

General options (single run or batch run mode)

.. _Psyco: http://psyco.sourceforge.net/

--optimise          Use Psyco optimisation. Requires Psyco_ to be installed.
                    (Note that using Psyco does not guarantee that processing
                    speed will be improved.)
                    
                    Abbreviation: ``-o``

--profile           Use cProfile around simulation run.
                    
                    Abbreviation: ``-p``

--verbose           Verbose level. 0=lowest, 5=highest. Defaults to the
                    value specified in the configuration file or 0.
                    
                    Abbreviation: ``-v``

Single "run" configuration mode

--config            A set of configuration names or plugins joined by plus
                    symbols (``+``). Items are applied in the order that they
                    appear.
                    
                    Abbreviation: ``-c``
                    
                    Example: ``-c RVP.Sphere+n2+GA``

--settings          Manually override any configuration setting. The parameter
                    must be a quoted string of parameter-value pairs, separated
                    by semicolons. Values are evaluated using ``eval`` and
                    assigned in the order that they appear.
                    
                    These overrides are applied after any settings specified
                    with ``--config``.
                    
                    Abbreviation: ``-s``
                    
                    Example: ``-s "system.size=200; random_seed=1"``

Multiple "batch" configuration model with logging of results

--batch             The name of a single batch file. This batch file must
                    exist in the ``cfgs`` directory with an identical name
                    (including case) and a ``.py`` extension.
                    
                    Abbreviation: ``-b``

'''

__docformat__ = 'restructuredtext'

from esec.utils import ConfigDict, settings_split, is_ironpython
from esec.utils.exceptions import ExceptionGroup
from esec import Experiment
from esec.monitors import ConsoleMonitor, CSVMonitor, MultiMonitor, MultiTarget
from esec.landscape import LANDSCAPES
from warnings import warn
import time, optparse, sys, os, collections
import dialects
from StringIO import StringIO

HR = '-' * 120 + '\n'# Horizontal rule

#==============================================================================

default = {
    'random_seed': 12345,
    'monitor': {
        'class': ConsoleMonitor,
        'limits': { 'generations': 10 },
    },
    'landscape': { 'random_seed': 12345 },
    'verbose': 0
}
'''`default` contains the base configuration that will be passed to
`Experiment`. The ``--config`` (``-c``) and ``--settings`` (``-s``)
options may be used to override parts of this configuration.
'''

configs = {
    'noseed': { 'random_seed': None },
    'landscape_noseed': { 'landscape': { 'random_seed': None } },
    
    'debug': { 'verbose': 5 },
    
    'csv': { 'monitor': {
        'class': CSVMonitor,
        'report_out': 'results/%04d.csv',
        'summary_out': 'results/%04d._summary.csv',
        'config_out': 'results/%04d._config.txt',
        'error_out': sys.stderr,
    } },
    
    'short': { 'monitor': { 'limits': { 'generations': 10 } } },
    'long': { 'monitor': { 'limits': { 'generations': 100 } } },
    'infinite': { 'monitor': { 'limits': { 'generations': None } } },
    
    'n2' : { 'landscape': { 'parameters': 2 } },
    'n3' : { 'landscape': { 'parameters': 3 } },
    'n10' : { 'landscape': { 'parameters': 10 } },
    'n100' : { 'landscape': { 'parameters': 100 } },
    'i': { 'landscape': { 'invert': True } },
}
'''`configs` contains a set of mappings from strings to configuration
overlays.

When executing ``run.py`` with the ``--config`` (``-c``) option, the
string passed is used to select and overlay these dictionarys over the
configuration passed to `Experiment`.
'''

# Add keys collected from landscape types
# Defined as a function to keep variables local
def _import_landscapes():
    '''Imports all default landscapes.'''
    for lscape in LANDSCAPES:
        name = lscape.ltype + "." + lscape.__name__
        configs[name] = { 'landscape': { 'class': lscape } }
_import_landscapes()

# Add keys collected from dialects
default.update(dialects.default)
configs.update(dialects.configs)

#==============================================================================

def _load_module(folder, mod_name):
    '''Loads a module. Has improved error handling that reveals more
    detail than `ImportError`.
    '''
    py_source = os.path.join(folder, mod_name + '.py')
    if os.path.exists(py_source):
        # This is a standard plugin file
        
        with open(py_source) as source:
            code_object = compile(source.read(), mod_name, 'exec')
        
        items = {}
        exec code_object in items   #pylint: disable=W0122
        
        return {
            'batch': items.get('batch', None),
            'config': items.get('config', None),
            'configs': items.get('configs', None),
            'defaults': items.get('defaults', None),
            'settings': items.get('settings', None),
        }
    else:
        return None


def _load_config(config_string, defaults):
    '''Loads a configuration from a configuration string.
    '''
    cfg = ConfigDict(defaults)
    for name in (o for o in config_string.split('+') if o):
        # Get name from configs
        if name in configs: 
            cfg.overlay(configs[name])
        # Get name from current configuration
        elif name in cfg:
            cfg.overlay(cfg[name])
        # Attempt to load module from cfgs or plugins
        else:
            mod = _load_module('cfgs', name) or _load_module('plugins', name)
            if not mod: raise ImportError('Cannot find ' + name + ' as configuration or plugin.')
            
            mod_cfg1 = mod.get('configs', None)
            mod_def = mod.get('defaults', None)
            mod_cfg2 = mod.get('config', None)
            if mod_cfg1: configs.update(mod_cfg1)
            if mod_def: cfg.overlay(mod_def)
            if mod_cfg2: cfg.overlay(mod_cfg2)
    return cfg


def _set_low_priority():
    '''Sets the current Python process to run at low priority.
    
    Currently only implemented for Windows (where ``sys.platform``
    is ``'win32'``).
    '''
    if sys.platform == 'win32':
        from ctypes import windll, c_voidp, c_ulong
        windll.kernel32.SetPriorityClass.argtypes = [ c_voidp, c_ulong ]
        windll.kernel32.SetPriorityClass(-1, 0x00004000)
    elif sys.platform == 'cli':
        from ctypes import windll
        windll.kernel32.SetPriorityClass(-1, 0x00004000)
    else:
        warn("Don't know how to set low priority for " + sys.platform)

#==============================================================================
# Run a single configuration
#==============================================================================
def esec_run(options):
    '''Load a system configuration with results sent directly to the console
    or automatically named CSV files in results/.
    
    The configuration can be specified firstly by the ``-c`` option and either
    built-in configuration names, names of configuration files saved in cfgs/
    or the name of a plugin file or package saved in plugins/.
    
    Settings specified with the ``-s`` option, are overlaid in the order
    specified.
    
    For example::
        
        > python run.py -c RVP.Sphere+n3+i+MyCFG01 -s "system.size=100"
    
    This creates an instance with:
    - the real-valued (RVP) `Sphere` landscape
    - n3, which sets ``landscape.parameters`` to 3,
    - i, which sets ``landscape.invert`` to ``True``,
    - any settings stored in ``cfgs/MyCFG01.py``, and
    - ``system.size`` set to 100 (overwriting any previous setting).
    
    Note that in this example MyCFG01.py would need to contain a system
    definition, since no built-in dialect is specified.
    '''
    
    print "  ** Configuration names: ", options.config
    
    # Loading defaults and the configuration names specified.
    cfg = _load_config(options.config, default)
    
    # Level of messages/information to show
    if options.verbose >= 0:
        cfg.verbose = int(options.verbose)
    
    # Display all the built-in configuration names
    if cfg.verbose >= 5:
        print HR
        print '## Config defaults:', configs
    
    # Use settings to override configuration parameters
    settings = settings_split(options.settings)
    for key, value in settings.items():
        cfg.set_by_name(key, value)
        if cfg.verbose >= 4:
            print 'Overriding: "%s" with "%s"' % (key, value)
    
    # Specify monitor verbosity (if it hasn't been yet)
    if 'verbose' not in cfg.monitor:
        cfg.monitor['verbose'] = cfg.verbose or 0
    
    # Start the experiment
    try:
        ea_app = Experiment(cfg)
    except ExceptionGroup:
        # Display any grouped errors nicely - they are probably syntax errors
        # in the system definition.
        ex = sys.exc_info()[1]
        print >> sys.stderr, HR, "Errors occurred:"
        print >> sys.stderr, ' ' + '\n '.join(str(i) for i in ex.exceptions)
        print >> sys.stderr, HR
        return
    
    # Run the application (and time it)
    start_time = time.clock()
    ea_app.run()
    print '->> DONE <<- in ', (time.clock() - start_time)


#==============================================================================
# Batch processing...
#==============================================================================
batch_settings_syntax = {
    'dry_run': bool,
    'start_at': int,
    'stop_at': int,
    'include_tags': [list, tuple, set, str, None],
    'exclude_tags': [list, tuple, set, str, None],
    'pathbase?': str,
    'summary': bool,
    'csv': bool,
    'low_priority': bool,
    'quiet': bool,
}
'''The syntax used for batch configurations.'''

batch_settings_default = {
    'dry_run': False,
    'start_at': 0,
    'stop_at': sys.maxint,
    'include_tags': None,
    'exclude_tags': None,
    'summary': True,
    'csv': False,
    'low_priority': False,
    'quiet': False,
}
'''The default values used for batch configurations.'''

def esec_batch(options):
    '''Runs a batch file of configurations and saves the results.
    
    Results are saved to::
    
        ./results/batchname/<index>.* data files
    
    A summary file of the batch and associated tags is saved in::
    
        ./results/batchname/_tags.(txt|csv)
    
    A summary file of the summary line from each experiment is saved in::
    
        ./results/batchname/_summary.(txt|csv)
    
    Data is (depending on settings) saved or appended to files::
    
        ./results/batchname/<id>._config.txt        # full config details
        ./results/batchname/<id>._summary.(txt|csv) # appended run results
        ./results/batchname/<id>.<run>.(txt|csv)    # per gen step results
    
    Handy ``run.py`` settings (-s "...") for batch runs include::
        
        batch.dry_run=True # create each configuration to test that they work but does nothing.
        batch.start_at=... # configuration id to start at. Will run the start_at id.
        batch.stop_at=... # configuration id to stop at. Will run the stop_at id, but not after it.
        batch.include_tags=[...] # only run experiments that include these "tags"
        batch.exclude_tags=[...] # do not run experiments that include these "tags"
        batch.pathbase="..." # relative path to store results in
        batch.summary=True # create a summary file of all experiments
        batch.csv=True # create CSV files instead of TXT files (except for config)
        batch.low_priority=True # run with low CPU priority
        batch.quiet=True # hide console output
    
    '''
    # Disable pylint complaints about branches and local variables
    #pylint: disable=R0912,R0914
    
    options.batch, _, tag_names = options.batch.partition('+')
    # A batch file is a normal .py file with a method named "batch" that 
    # returns a sequence of tuples of settings.
    mod = _load_module('cfgs', options.batch)
    # Update configs with anything specified in the batch file
    configs.update(mod.get('configs', None) or { })
    # Get any settings overrides from the batch file
    batch = mod.get('batch')()
    batch_settings = mod.get('settings', '')
    # Get config defaults (allows batch files to import plugins directly)
    batch_default = ConfigDict(default)
    batch_default.overlay(mod.get('defaults', { }))
    
    print '>>>>', batch_settings
    
    # Initialise batch settings
    batch_cfg = ConfigDict(batch_settings_default)
    batch_cfg.pathbase = os.path.join('results', options.batch)
    
    # Handle any extra settings
    batch_cfg.overlay(settings_split(batch_settings))
    
    for key, value in settings_split(options.settings).iteritems():
        # Only want batch settings, and don't want the "batch." prefix
        if key.startswith('batch.'):
            batch_cfg[key[6:]] = value
    
    # Ensure the batch syntax is valid. Exit if errors and warn on
    # keys that aren't in the syntax.
    errors, other_keys = batch_cfg.validate(batch_settings_syntax)
    if errors:
        print >> sys.stderr, "Batch configuration settings are invalid:"
        print >> sys.stderr, '  ' + '\n  '.join(str(ex) for ex in errors)
        return
    elif other_keys:
        print >> sys.stderr, "Batch configuration contains unknown settings:"
        print >> sys.stderr, '  ' + '\n  '.join('%s: %r' % (key, batch_cfg[key]) for key in other_keys)
        print >> sys.stderr
    
    if isinstance(batch_cfg.include_tags, str): batch_cfg.include_tags = batch_cfg.include_tags.split('+')
    if isinstance(batch_cfg.exclude_tags, str): batch_cfg.exclude_tags = batch_cfg.exclude_tags.split('+')
    batch_cfg.include_tags = set(batch_cfg.include_tags or set())
    batch_cfg.exclude_tags = set(batch_cfg.exclude_tags or set())
    
    if tag_names:
        tag_names = tag_names.split('+')
        batch_cfg.include_tags.update(t for t in tag_names if t[0] != '!')
        batch_cfg.exclude_tags.update(t[1:] for t in tag_names if t[0] == '!')
    
    # Output file extension is '.txt' unless the csv setting is True.
    extension = '.txt'
    if batch_cfg.csv:
        extension = '.csv'
    
    # Lower the process priority if requested.
    if batch_cfg.low_priority:
        _set_low_priority()
    
    # Create a directory for results and warn if already exists
    pathbase = os.path.abspath(batch_cfg.pathbase)
    try:
        # makedirs creates the path recursively.
        os.makedirs(pathbase)
    except OSError:
        warn('Output folder already exists and may contain output from a previous run (%s)' % pathbase)
    
    # Is this a tag summary run?
    if batch_cfg.include_tags or batch_cfg.exclude_tags:
        # Generate a summary file of cfgids, tags and format strings
        tags_file = open(os.path.join(pathbase, '_tags' + extension), 'w')
        if batch_cfg.csv:
            tags_file.write("Id,Tags,Format\n")
        else:
            tags_file.write("# id, tags and format strings. \n")
        # Track tags and the ids that match them
        summary_tags = collections.defaultdict(list)
    
    # Create a super summary (summary of the summary lines)
    summary_file = open(os.path.join(pathbase, '_summary' + extension), 'w')
    
    # Run each configuration of the batch
    for i, batch_item in enumerate(batch):
        # Use get method (dictionary) if available;
        # otherwise, assume compatibility mode (tuple).
        if hasattr(batch_item, 'get'):
            tags = batch_item.get('tags', set([]))
            names = batch_item.get('names', None)
            config = batch_item.get('config', None)
            settings = batch_item.get('settings', None)
            fmt = batch_item.get('format', None) or batch_item.get('fmt', None)
        else:
            tags, names, config, settings, fmt = batch_item
        
        # Use cfgid instead of converting i repeatedly
        cfgid = '%04d' % i
        if batch_cfg.include_tags or batch_cfg.exclude_tags:
            if tags:
                # Write the summary of cfgid, tags and format string.
                if batch_cfg.csv:
                    tags_file.write('%d,"%s","%s"\n' % (i, tags, fmt))
                else:
                    tags_file.write("%s; %s; %s\n" % (cfgid, tags, fmt))
                # Track the cfgid against the tags listed (all printed later)
                for tag in tags:
                    summary_tags[tag].append(cfgid)
            else:
                # Write the summary of cfgid and format string.
                if batch_cfg.csv:
                    tags_file.write('%d,,"%s"\n' % (i, fmt))
                else:
                    tags_file.write("%s; ; %s\n" % (cfgid, fmt))
        # Start and stop limits?
        if i < batch_cfg.start_at: continue
        if i > batch_cfg.stop_at: break
        # Include/exclude list?
        if batch_cfg.include_tags and not batch_cfg.include_tags.intersection(tags) \
        or batch_cfg.exclude_tags and batch_cfg.exclude_tags.intersection(tags):
            continue
        # Print an obvious header
        print '\n** ' + "*"*117
        print ' **'
        print ("  ** Experiment %04d." % i), (("Tags %s" % tags) if tags else "")
        print ' **'
        print "** "+ "*"*117 + '\n'
        
        # Overlay any configuration names specified for this run.
        try:
            cfg = _load_config(names, batch_default)
        except AttributeError:
            print >> sys.stderr, 'Loading config file(s) failed: '+ names
            raise
        # Overlay any config dictionary (copy to avoid shared reference issues)
        cfg.overlay(ConfigDict(config) if isinstance(config, ConfigDict) else config)
        # Override cfg.verbose
        if options.verbose >= 0:
            cfg.verbose = int(options.verbose)
        # Use settings strings to override configurations
        for key, value in settings_split(settings).iteritems():
            cfg.set_by_name(key, value)
        
        # Write summary to a buffer first, then only include the second line
        # in the super summary file (ignore headings)
        summary_buffer = StringIO()

        # Helper function to open a unique file
        def _open(filepattern, mode='w'):
            '''Returns an open file. `filepattern` must contain a ``%d`` value so
            a unique index may be included.'''
            i = 0
            filename = filepattern % i
            # Not reliable, but no other choice in Python
            # (specifically, open() has no way to fail when a file exists)
            while os.path.exists(filename):
                i += 1
                filename = filepattern % i
            return open(filename, mode)
        
        # Close files/objects in this list after this run
        open_files = []
        
        # If the monitor has been specified as a dictionary, specify output files.
        # If the monitor has been specified directly, don't try and change it.
        if isinstance(cfg.monitor, (ConfigDict, dict)):
            report_out = _open(os.path.join(pathbase, cfgid + '.%04d' + extension))
            summary_out = _open(os.path.join(pathbase, cfgid + '.%04d._summary' + extension))
            config_out = _open(os.path.join(pathbase, cfgid + '.%04d._config.txt'))
            open_files.extend((report_out, summary_out, config_out))
            
            if not batch_cfg.csv:
                if batch_cfg.quiet:
                    # MultiTarget sends the same output to both the console and the files.
                    cfg.overlay({'monitor': {
                        'report_out': report_out,
                        'summary_out': MultiTarget(summary_out, sys.stdout, summary_buffer),
                        'config_out': config_out,
                        'error_out': MultiTarget(summary_out, sys.stderr),
                        'verbose': max(4, cfg.verbose),
                    }})
                else:
                    # MultiTarget sends the same output to both the console and the files.
                    cfg.overlay({'monitor': {
                        'report_out': MultiTarget(report_out, sys.stdout),
                        'summary_out': MultiTarget(summary_out, sys.stdout, summary_buffer),
                        'config_out': MultiTarget(config_out, sys.stdout),
                        'error_out': MultiTarget(summary_out, sys.stderr),
                        'verbose': max(4, cfg.verbose),
                    }})
            else:
                # MultiMonitor sends the same callbacks to different monitors.
                monitor_cfg = ConfigDict(cfg.monitor)
                if batch_cfg.quiet:
                    monitor_cfg['report_out'] = None
                    monitor_cfg['config_out'] = None
                console_monitor = ConsoleMonitor(monitor_cfg)
                monitor_cfg.overlay({
                    'report_out': report_out,
                    'summary_out': MultiTarget(summary_out, summary_buffer),
                    'config_out': config_out,
                    'error_out': summary_out,
                    'verbose': max(4, cfg.verbose),
                })
                csv_monitor = CSVMonitor(monitor_cfg)
                
                cfg.monitor = {
                    'class': MultiMonitor,
                    'monitors': [ console_monitor, csv_monitor ]
                }
        
        # Create an Experiment instance
        ea_exp = Experiment(cfg)
        
        # Run the application (and time it)
        if not batch_cfg.dry_run:
            start_time = time.clock()
            ea_exp.run()
            print '->> DONE <<- in ', (time.clock() - start_time)
        else:
            print '--> DRY RUN DONE <--'
        
        # Write the summary to the super summary file.
        if summary_file and not batch_cfg.dry_run:
            summary_lines = summary_buffer.getvalue().splitlines()[:2]
            if batch_cfg.csv:
                if i == 0:
                    summary_file.write('#,' + summary_lines[0] + '\n')
                summary_file.write('%d,%s\n' % (i, summary_lines[1]))
            else:
                if i == 0:
                    summary_file.write('  #  ' + summary_lines[0] + '\n')
                summary_file.write('%04d %s\n' % (i, summary_lines[1]))
            summary_file.flush()
        
        for obj in open_files: obj.close()
        
    # Save the tag data
    if batch_cfg.include_tags or batch_cfg.exclude_tags:
        tags_file.write("#\n# Summary of cfgid's per tag\n#\n")
        if batch_cfg.csv:
            for tag in sorted(summary_tags.keys()):
                tags_file.write(tag+','+','.join(str(s) for s in summary_tags[tag])+'\n')
        else:
            for tag in sorted(summary_tags.keys()):
                tags_file.write(tag+'='+str(summary_tags[tag])+'\n')
        tags_file.close()
        print 'Tag Run done!'

#==============================================================================
# Entry point
#==============================================================================

def main():
    '''The main entry point for ``run.py``.
    '''
    # Banner
    print HR,
    print ' ESEC: EcoSystem Evolutionary Computation'
    print ' Copyright (c) Clinton Woodward and Steve Dower 2007-2010'
    print HR
    
    # Check for arguments
    parser = optparse.OptionParser()
    # Options are ...
    parser.add_option('-o', '--optimise', action="store_true", default=False,
                      help='use psyco optimisation')
    parser.add_option('-p', '--profile', action="store_true", default=False,
                      help='use cProfile around simulation run')
    parser.add_option('-v', '--verbose', action="store", type="int", default="-1",
                      help='verbose level. 0=lowest, 5=highest. (Default config.)')
    # Single run settings
    parser.add_option('-c', '--config', metavar="NAMES", default='',
                      help='A set of configuration NAMES joined by "+" ')
    parser.add_option('-s', '--settings', metavar="NAMES", default='',
                      help='Override config settings. Quote and separate with ;.\n'+
                           'Values are eval()uated to support types.\n'+
                           'eg. -s "system.size=200; application.run_count=3" ')
    # Batch run setting
    parser.add_option('-b', '--batch', metavar="FILE", default='',
                      help='The name of a single batch file with optional\n'+
                           'tags joined by "+". Prefix tags with "!" to\n'+
                           'exclude them.')
    
    # Keep the processed options and any remaining items
    options, _ = parser.parse_args()
    
    # Ignore some options under IronPython
    if is_ironpython():
        if options.optimise:
            warn("Cannot use Psyco under IronPython")
            options.optimise = False
        if options.profile:
            warn("Cannot profile under IronPython")
            options.profile = False
    
    # Optimise using Psyco?
    if options.optimise:
        try:
            import psyco
            psyco.full()
            print '  ** Psyco Optimisation! **'
        except ImportError:
            warn("Cannot import Psyco")
    
    # Batch run?
    if options.batch:
        esec_op = esec_batch
    # Single run?
    else:
        esec_op = esec_run
    
    # Profile this run?
    if options.profile:
        from cProfile import Profile
        print '  ** With profiling **'
        profiler = Profile()
        try:
            profiler.runcall(esec_op, options)
        finally:
            # Messy but necessary to redirect the profiler output to stderr instead
            # of stdout.
            import pstats
            pstats.Stats(profiler, stream=sys.stderr).sort_stats(-1).print_stats()
    else:
        esec_op(options)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print HR
        if is_ironpython():
            # sys.exit() under IronPython closes the console window.
            # Re-raising will return to interactive mode (if -i is used)
            raise
        else:
            sys.exit()
