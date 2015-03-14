# Batch and Configuration Files

Configuration files provide reproducible automation of esec over both single and multiple experiments. Files that specify a single run are called configuration files, while those that specify multiple runs are batch files. 

Batch and configuration files are Python scripts stored in the `esec/cfgs` directory. Despite the distinguishing terminology, a single file can be both a configuration and a batch file.

Configuration files are functionally identical to [plug-ins](Plugins.md), though they typically provide only configuration details. This configuration is provided as a dictionary in the variable `config` (which behaves identically to `defaults` in a plug-in) that is overlaid onto the active configuration when the configuration file is loaded.

Batch files provide a method `batch()`, which takes no parameters and returns a list or sequence of dictionaries (or any object with a `get(key, default)` method) that specify each experiment to run.

The content of each dictionary is:

| *Key* | *Value* |
| ----- | ------- |
| `tags` | A sequence of tag strings identifying the experiment category. |
| `names` | A set of configuration names as for `--config`. |
| `config` | A pre-initialised dictionary of configuration settings. |
| `settings` | A parameter override string as for `--settings`. |
| `format` | A format string to display in the tag summary file. |

Elements not provided are assumed to be `None` (the Python keyword representing no value). `None` is a valid value for any element.

Tag strings are used to simplify the process of running a limited part of a batch file. For example, a batch file that uses a number of sets of parameters may identify each set with a tag, providing a simple mechanism for running one set at a time. Each configuration may have multiple tags: if any of these are specified in `include_tags` and none of them is specified in `exclude_tags`, the configuration will be included in the run.

Tags may also be specified on the command line as part of the parameter to the `--batch` switch. After the name of the batch file (which must always appear first), tags may be appended separated by plus (`+`) characters. Tag names prefixed with an exclamation mark (`!`) are excluded from the run, while others are included.

Batch files support an extra set of settings that control which experiments to run. When provided on the command line with the `--settings` option, the setting name must be prefixed with `batch.`, for example, `batch.dry_run=True`. When provided in the `settings` variable in the batch file, `dry_run=True` has the same effect.

| *Setting* | *Description* |
| --------- | ------------- |
| `dry_run` | If `True`, creates all experiments but does not run any of them. |
| `start_at` | The index of the first experiment to run. |
| `stop_at` | The index of the last experiment to run. |
| `include_tags` | A list of tags specifying which experiments to run. These may also be specified on the command line by appending `+tag` to the `--batch` switch. |
| `exclude_tags` | A list of tags specifying which experiments to ignore. These may also be specified on the command line by appending `+!tag` to the `--batch` switch. |
| `pathbase` | A directory path relative to run.py to store results in. |
| `csv` | If `True`, writes CSV formatted files. |
| `summary` | If `True`, creates a summary of the entire batch results. |
| `low_priority` | If `True`, runs the Python process at low CPU priority. |
| `quiet` | If `True`, only summaries of each experiment are displayed to the console. |
