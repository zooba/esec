#   Copyright 2010 Steve Dower
# 
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

'''An Ant Colony Optimsation (ACO) plugin.
'''

import pheromone
import tsp

#==============================================================================

# Add known species classes to the list of available species types
import esec.species
esec.species.include(tsp.TourSpecies)

#==============================================================================

# A definition for a simple system for TSP.
TSP_DEF = r'''
cost_map = config.landscape.cost_map
pheromone_map = create_pheromone_map(initial=0.1)

BEGIN GENERATION
    FROM build_tours(cost_map=cost_map, cost_power=2, \
                     pheromone_map=pheromone_map, pheromone_power=2) \
        SELECT (size) ants
    YIELD ants
    
    pheromone_map.update_fitness(source=ants, persistence=0.9, strength=100, minimisation=True)
END GENERATION
'''

#==============================================================================

configs = {
    # The ACO.TSP configuration name may be used to load settings for running the TSP problem.
    'ACO.TSP': {
        'landscape': {
            'class': tsp.Landscape,
        },
        'system': {
            'definition': TSP_DEF,
            'create_pheromone_map': pheromone.PheromoneMap
        },
        'monitor': {
            'primary': 'ants',
            'report': 'brief_int+local_header+local_min_int+local_ave+local_max_int+|+time_delta'
        },
    },
    # The berlin52 configuration name specifies the cost settings associated with the TSP landscape.
    'berlin52': {
        'landscape': {
            'cost_map': tsp.Landscape.berlin52_map,
        },
        'monitor': {
            'limits': {
                'fitness': 7542
            }
        }
    }
}

#==============================================================================

defaults = {
    'system': {
        'size': 100,
    }
}