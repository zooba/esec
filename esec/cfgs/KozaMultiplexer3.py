#   Copyright 2010 Clinton Woodward and Steve Dower
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

from esec.landscape import tgp

config = {
    'landscape': {
        'class': tgp.Multiplexer,
        'parameters': 3,
    },
    'system': { 
        'definition': r'''
            FROM boolean_tgp(terminals=11, deepest=4) SELECT (size) population
            YIELD population

            BEGIN generation
                FROM population SELECT (0.9*size) to_cross, (0.08*size) to_reproduce, (0.02*size) to_mutate \
                     USING fitness_proportional
                
                FROM to_cross SELECT offspring1 USING crossover_one(deepest_result=15, terminal_prob=0.1)
                FROM to_mutate SELECT offspring2 USING mutate_random(deepest_result=15)
                
                FROM offspring1, offspring2, to_reproduce SELECT population \
                     USING mutate_edit(per_indiv_rate=0.1)
                
                YIELD population
            END generation
        ''',
        'size': 4000
    },
    'monitor': {
        'report': 'gen+births+best+local+best_length+time_delta',
        'summary': 'status+best+best_length+best_phenome',
        'limits': {
            'generations': 100,
            'fitness': tgp.TGPFitness([2048.0, 20]),
        }
    },
}

pathbase = 'results/KozaMultiplexer3'
import os.path
i = 0
while os.path.exists(pathbase):
    i += 1
    pathbase = 'results/KozaMultiplexer3_%02d' % i

settings = ''
settings += 'pathbase="%s";' % pathbase
settings += 'csv=False;low_priority=True;quiet=True;'

def batch():
    for i in xrange(0, 500):
        yield { 'config': config, 'settings': "random_seed=%d" % i }
