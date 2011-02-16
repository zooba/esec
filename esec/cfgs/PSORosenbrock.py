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

from plugins.PSO import *

SYSTEM_DEFINITION = r'''
FROM random_pso(length=(n), lowest=(init_lower), highest=(init_upper), \
                position_lower_bound=-100, position_upper_bound=100, \
                velocity_lower_bound=-100, velocity_upper_bound=100) \
        SELECT (size) population
EVAL population USING rosenbrock
FROM population SELECT 1 global_best USING best_only
FROM population SELECT (size) p_bests
YIELD population

inertia = 0.9
inertia_step = (0.9 - 0.4) / limit

BEGIN GENERATION
    JOIN population, p_bests INTO pairs USING tuples
    
    FROM pairs SELECT population USING update_velocity(global_best=global_best, w=inertia), \
                                       update_position_clamp
    
    JOIN population, p_bests INTO pairs USING tuples
    FROM pairs SELECT p_bests USING best_of_tuple
    
    FROM population, global_best SELECT 1 global_best USING best_only
    
    YIELD global_best, population
    inertia = inertia - inertia_step
END GENERATION
'''

from esec import esdl_eval

@esdl_eval
def rosenbrock(indiv):
    fitness = 0.0
    x = indiv[0]
    for y in indiv[1:]:
        fitness += 100*(y-x*x)*(y-x*x) + (x-1)*(x-1)
        x = y
    return -fitness

config = {
    'system': {
        'definition': SYSTEM_DEFINITION,
        #'rosenbrock': Rosenbrock, #(),
        'size': 80,
        'n': 10,
        'init_lower':-30,
        'init_upper': 30,
        'limit': 1000,
    },
    'monitor': {
        'report': 'brief+local+time_delta',
        'summary': 'status+brief+best_genome',
        'limits': {
            'generations': 1000,
        }
    },
}

pathbase = 'results/PSORosenbrock_00'
import os.path
i = 0
while os.path.exists(pathbase):
    i += 1
    pathbase = 'results/PSORosenbrock_%02d' % i

settings = ''
settings += 'pathbase="%s";' % pathbase
settings += 'csv=True;low_priority=True;'

def batch():
    for pop in (20, 40, 80, 160):
        for n, limit in zip((10, 20, 30), (1000, 1500, 2000)):
            for _ in xrange(50):
                yield (
                    ["pop%dn%d" % (pop, n), "pop%d" % (pop)],
                    "PSORosenbrock+noseed",
                    {
                        "system":
                        {
                            "size": pop,
                            "n": n,
                            "limit": limit,
                            "init_lower": 15.0,
                            "init_upper": 30.0,
                        },
                        "monitor": { "limits": { "generations": limit } },
                    },
                    None,
                    None)
