# Command-Line Options #
These command-line options are for use with the `run.py` script. Applications that directly import or host esec are not required to support or imitate these options.

## General Options ##
| **Option** | | **Description** |
|:-----------|:|:----------------|
| `--optimise` | `-o` | Uses Psyco optimisation if available `[1]`. (Note that using Psyco does not guarantee that processing speed will improve.) |
| `--profile` | `-p` | Uses cProfile during a single simulation run. (Profiling is not supported under IronPython.) |
| `--verbose` | `-v` | Sets the verbosity level. Valid levels are 0 through 5 (inclusive), where zero provides experiment output only and five provides full debugging information. |

`[1]` It is also worth using Python's `-O` option (written as `python -O run.py ...`) which will disable a large number of assertions.

## Single-Run Options ##
| **Option** | | **Description** |
|:-----------|:|:----------------|
| `--config` | `-c` | Specifies a set of [configuration names](ConfigurationNames.md) or [plug-ins](Plugins.md) joined by plus symbols ('+'). Items are applied in the order that they appear.<br />Example: `-c RVP.Sphere+n3+GA` |
| `--settings` | `-s` | Manually override any configuration setting. The parameter must be a quoted string of parameter-value pairs, separated by semicolons. Values are evaluated using Python's `eval` method and assigned in the order that they appear.<br />These overrides are applied after any settings specified with `--config`.<br />Example: `-s "system.size=200; random_seed=1"` |

## Batch Options ##
| **Option** | | **Description** |
|:-----------|:|:----------------|
| `--batch` | `-b` | Specifies the name of a single [batch file](BatchFiles.md) and any tags to include or exclude. This batch file must exist in the `cfgs` directory with an identical name (including case) and a `.py` extension.<br />Example: `-b KozaMultiplexer3+pop100` |