#   Copyright 2010-2011 Steve Dower
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

city_graph = esec.landscape.sequence.TSP(cost_map="cfgs/TSP/Oliver30.csv")

config = {
    'system': {
        'alpha': 1.0,
        'beta': 5.0,
        'rho': 0.5,
        'Q': 100,
        'colony_size': 30,
        'cost_map': city_graph.cost_map,
        'city_graph': city_graph,
        'definition': r'''
            pheromone_map = create_pheromone_map(initial=(0.1))
            
            BEGIN GENERATION
                FROM build_tours(cost_map, cost_power=(beta), \
                                 pheromone_map, pheromone_power=(alpha)) \
                    SELECT (colony_size) ants
                
                EVAL ants USING city_graph
                YIELD ants
                
                pheromone_map.update(source=ants, persistence=(rho), strength=(Q), minimisation)
            END GENERATION
        ''',
        'create_pheromone_map': plugins.ACO.pheromone.PheromoneMap,
    },
    'monitor': {
        'report': 'brief+local_header+local_min+local_ave+local_max+local_unique+|+time',
        'summary': 'status+brief+best_phenome',
        'limits': {
            'fitness': 423.8,
            'iterations': 2500,     # while NC < 2500
            'unique': 1,            # stagnation
        },
        'primary': 'ants',
    },
}

pathbase = 'results/TSPOliver30_00'
import os.path
i = 0
while os.path.exists(pathbase):
    i += 1
    pathbase = 'results/TSPOliver30_%02d' % i

settings = ''
settings += 'pathbase="%s";' % pathbase
settings += 'csv=True;low_priority=True;quiet=True'

def batch():
    config['monitor']['limits'] = { 'iterations': 5000 }
    config['monitor']['report'] = 'brief+local+time_precise'
    for alpha in [0, 0.5, 1, 2]:
        for i in xrange(10):
            yield (['alpha'], "noseed", config, "system.alpha=%f" % alpha, None)
    for beta in [0, 0.5, 1, 2]:
        for i in xrange(10):
            yield (['beta', 'beta1'], "noseed", config, "system.beta=%f" % beta, None)
    for beta in [5, 10, 20]:
        for i in xrange(10):
            yield (['beta', 'beta2'], "noseed", config, "system.beta=%f" % beta, None)
    for rho in [0.3, 0.5, 0.7, 0.9]:
        for i in xrange(10):
            yield (['rho'], "noseed", config, "system.rho=%f" % rho, None)

