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

import esec.landscape.sequence

config = {
    'landscape': {
        'class': esec.landscape.sequence.TSP,
        'cost_map': "cfgs/TSP/Oliver30.csv",
    },
    'system': {
        'size': 100,
        'definition': r'''
            FROM random_sequence(length=config.landscape.size) SELECT (size) population
            YIELD population
            
            BEGIN generation
                FROM population SELECT (size) parents USING \
                    tournament(k=2, greediness=0.8)
                
                FROM parents SELECT (size) offspring USING \
                    crossover(per_pair_rate=0.5), \
                    repair(randomly), \
                    mutate_random(per_gene_rate=0.1)
                
                FROM population, offspring SELECT (size) population USING \
                    best
                
                YIELD population
            END
        ''',
    },
    'monitor': {
        'report': 'brief+local_header+local_min+local_ave+local_max+|+time',
        'summary': 'status+brief+best_phenome',
        'limits': {
            'fitness': 423.8,
            'iterations': 100,
        },
    },
}

pathbase = 'results/TSPOliver30_2_00'
import os.path
i = 0
while os.path.exists(pathbase):
    i += 1
    pathbase = 'results/TSPOliver30_2_%02d' % i

settings = ''
settings += 'pathbase="%s";' % pathbase
settings += 'csv=True;low_priority=True;quiet=True'

def batch():
    while True:
        yield { 'config': config }
