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

import plugins.ACO
import esec.landscape.sequence

config = {
    'system': {
        'definition': r'''
            cost_map = config.landscape.cost_map
            pheromone_map = create_pheromone_map(initial=0.1)

            BEGIN GENERATION
                FROM build_tours(cost_map=cost_map, cost_power=2, \
                                 pheromone_map=pheromone_map, pheromone_power=2) \
                    SELECT (size) ants
                YIELD ants
    
                pheromone_map.update_fitness(source=ants, persistence=0.9, \
                                             strength=10, minimisation=True)
            END GENERATION
        ''',
        'create_pheromone_map': plugins.ACO.pheromone.PheromoneMap,
        'size': 100,
    },
    'landscape': {
        'class': esec.landscape.sequence.TSP,
        'cost_map': esec.landscape.sequence.TSP.berlin52_map,
    },
    'monitor': {
        'report': 'brief+local_header+local_min+local_ave+local_max+local_unique+|+time_delta',
        'summary': 'status+brief+best_phenome',
        'limits': {
            'fitness': 7542,
        },
        'primary': 'ants'
    },
}

pathbase = 'results/TSPBerlin52_00'
import os.path
i = 0
while os.path.exists(pathbase):
    i += 1
    pathbase = 'results/TSPBerlin52_%02d' % i

settings = ''
settings += 'pathbase="%s";' % pathbase
settings += 'csv=True;low_priority=True;'

def batch():
    while True:
        yield ([], "noseed", config, None, None)
