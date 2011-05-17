#   Copyright 2011 Steve Dower
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
        'class': esec.landscape.sequence.SimplePacking,
        'item_sizes': [ 0.3, 0.5, 1.1, 1.4, 2.3, 2.3, 3.1, 3.4, 3.9, 4.7, 5.1, 5.6, 6.1, 6.8, 7.4, 7.4, 8.9, 9.3 ] * 10,
        'box_size': 9.3,
    },
    'system': {
        'size': 500,
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
            'fitness': 0,
            'iterations': 500,
        },
    },
}


pathbase = 'results/Packing_00'
import os.path
i = 0
while os.path.exists(pathbase):
    i += 1
    pathbase = 'results/Packing_%02d' % i

settings = ''
settings += 'pathbase="%s";' % pathbase
settings += 'csv=True;low_priority=True;quiet=True'

def batch():
    while True:
        yield { 'config': config }
