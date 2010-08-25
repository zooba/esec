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
        'class': tgp.SymbolicRegression,
        'expr': 'X**4+X**3+X**2+X',
    },
    'system': { 
        'definition': r'''
            FROM real_tgp(terminals=1, deepest=4, transcendentals=True, \
                          lowest_constant=-1.0, highest_constant=1.0) SELECT (size) population
            YIELD population

            BEGIN generation
                FROM population SELECT (size/10) preserved, (size-size/10) parents USING binary_tournament
                FROM parents SELECT offspring USING crossover_one(per_pair_rate=0.9, deepest_result=15), \
                                                    mutate_random(per_indiv_rate=1.0/(size), deepest_result=15), \
                                                    mutate_permutate(per_indiv_rate=1.0/(size)), \
                                                    mutate_edit(per_indiv_rate=0.5)
                FROM preserved, offspring SELECT population
                YIELD population
            END generation
        ''',
        'size': 300
    },
    'monitor': {
        'report': 'gen+births+best+local+best_length+time_delta',
        'summary': 'status+best+best_length+best_phenome',
        'limits': {
            'generations': 100,
            'fitness': tgp.TGPFitness([-0.1, 15]),
        }
    },
}

settings = ''
#settings += 'pathbase="";'
settings += 'csv=False;low_priority=True;'

def batch():
    for i in xrange(0, 500):
        yield ([], "KozaSymbolicRegression", None, "random_seed=%d" % i, None)
    