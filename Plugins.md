# Plug-ins #
Plug-ins allow esec to easily import added functionality in the form of scripts or packages. They are primarily intended for use with the `run.py` script but also simplify the programmatic initialisation of experiments. Plug-ins may include new or extended species, landscapes, dialects and configuration names, or modify the behaviour of existing settings.

Only one plug-in is intended to be loaded at any time, since there is only one set of configuration names. Loading multiple plug-ins may cause conflicting definitions and is not supported; however, a plug-in may import and explicitly expose other plug-ins.

The main plug-in file is a Python script or module stored in the `esec/plugins` directory. The (case-sensitive) name of the script or module is used as a [configuration name](ConfigurationNames.md) that loads the plug-in. (If developing a plug-in as a module, "plug-in script" refers to the `__init__.py` file of the module).

## Configuration Names ##

The plug-in script may provide a dictionary containing configuration names in a variable `configs`. The key of each element is the name and the value is a dictionary to overlay onto the current configuration. These elements are added to the set of known configuration names, replacing any previous elements with matching names.

A dictionary of default values may be included in a variable `defaults`. These values are overlaid onto the active configuration immediately and allow settings such as monitor formats and the system definition to be set to sensible defaults for the plug-in.

## Landscapes ##


New landscapes are exposed as configuration names. By convention, the name used is an abbreviation of the relevant species (such as BVP for binary valued problems or TGP for tree-based genetic programming), a period and the name of the landscape.

The value associated with the configuration name typically sets the `landscape.class` setting to the landscape type object, along with any other required settings.

```
import landscape.real
configs = {
    'RVP.Linear': {
        'landscape': {
            'class': landscape.real.Linear,
            'N': 5,
        },
    },
}
```

Alternatively, the landscape setting may be provided directly with an instance of an evaluator. This, however, prevents further customisation of the evaluator from the command line and is not recommended for plug-ins.

## Dialects ##


New dialects are exposed as configuration names. By convention, the name used is an appropriate acronym of the dialect's name (such as SSGA for Steady-State Genetic Algorithm or EP for Evolutionary Programming).

The value associated with the configuration name typically sets the `system.definition` setting to the ESDL code for the dialect, along with any other names or variables required by the system.

```
configs = {
    'GA': {
        'system': {
            'definition': r'''
FROM random_int(length=10) SELECT (size) population
YIELD population

BEGIN generation
    FROM population SELECT (size) offspring USING binary_tournament

    FROM offspring SELECT population USING crossover_one(per_indiv_rate=0.8), \
                                           mutate_random(per_indiv_rate=(1.0/size))

    YIELD population
END generation
            ''',
            'size': 10,
        },
    },
}
```

Values specified as variables (such as `size`, above) can be overridden by other configuration names or the `--settings` command line option; values specified directly in the definition (such as the individual length or the rate of crossover) cannot.

## Species ##
Species classes must be advertised to ensure that the breeding system is aware of any names exposed through its `public_context` variable (such as initialisation or mutation operators). Species are advertised by importing the main species package and calling `include`.

```
from species import RealSpecies, BinarySpecies

import esec.species
esec.species.include(RealSpecies, BinarySpecies)
```