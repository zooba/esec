# Configuration Names

Configuration names identify collections of settings to apply to the current experiment.  Names are used with the `--config` [command line option](CommandLine.md) to simplify single experiments, or with [batch files](BatchFiles.md) to make use of standard settings or [plug-ins](Plugins.md).

Plug-ins may add new configuration names, though these are only usable when the plug-in is specified.

## Built-in Names

| *Name* | *Description* |
| ------ | ------------- |
| noseed | Uses a time-dependent value to seed the breeding system’s random number generator (the default seed is 12345).<br/>(Note: Landscapes use a separate seed.) |
| landscape_noseed | Uses a time-dependent value to seed the landscape’s random number generator (the default landscape seed is 12345).<br/>(Note: Breeding systems use a separate seed.) |
| n2 | Sets the `parameters` setting of the landscape to 2.<br/>(Note: This setting is not used by all landscapes.) |
| n3 | Sets the `parameters` setting of the landscape to 3. |
| n10 | Sets the `parameters` setting of the landscape to 10. |
| n100 | Sets the `parameters` setting of the landscape to 100. |
| i | Uses an inverted fitness function for the landscape. |
| short | Restricts the experiment to ten generations. |
| long | Restricts the experiment to one hundred generations. |
| infinite | Removes any generation limit on the experiment. |
| debug | Sets the verbosity level to its highest setting (5). |
| csv | Selects the CSV monitor and directs output to automatically named files in the `results` directory. |
