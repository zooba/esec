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

from esec.utils import ConfigDict
from esec.landscape import ge

config = {
    'landscape': {
        'class': ge.SymbolicRegression,
        'size': { 'min': 4, 'max': 100 },
        'expr': 'X**4+X**3+X**2+X',
        'size_penalty_square_factor': 0.0,
        'size_penalty_linear_factor': 0.0,
    },
    'system': {
        'definition': r'''
FROM random_ge(grammar=default_grammar,defines=default_defines) SELECT (size) population
YIELD population

BEGIN generation
    REPEAT (size)
        FROM population SELECT 2 parents USING binary_tournament
        FROM parents    SELECT 1 offspring \
            USING crossover_one_different(per_pair_rate=0.9,longest_result=config.landscape.size.max), \
                  mutate_insert(per_indiv_rate=0.1, longest_result=config.landscape.size.max), \
                  mutate_random(per_gene_rate=0.01), \
                  best
        
        FROM population      SELECT 1 replacee, rest USING uniform_shuffle
        FROM offspring, rest SELECT population
    END REPEAT
    
    YIELD population
END generation''',
        'size': 500,
        'default_defines': ge.SymbolicRegression.defines,
        'default_grammar': ge.SymbolicRegression.rules,
    },
    'monitor': {
        'report': 'brief+local+best_length+time',
        'summary': 'status+brief+best_phenome',
        'limits': {
            'generations': 10000,
            'fitness': 0.2,
            'stable': 100,
        }
    },
}

pathbase = 'results/ONeillSymbolicRegression'
import os.path
i = 0
while os.path.exists(pathbase):
    i += 1
    pathbase = 'results/ONeillSymbolicRegression_%02d' % i

settings = ''
settings += 'pathbase="%s";' % pathbase
settings += 'csv=True;low_priority=True;'

def batch():
    while True:
        yield ([], "ONeillSymbolicRegression+noseed", None, None, None)

