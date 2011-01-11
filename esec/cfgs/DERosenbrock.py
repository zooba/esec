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

from esec import esdl_func
from esec.utils import ConfigDict
from esec.landscape import real

@esdl_func
def mutate_DE(_source, scale=0.8):
    '''A generator that yields one mutated Individual for every JoinedIndividual
    passed in source.
    '''
    for joined_individual in _source:
        base, parameter1, parameter2 = joined_individual[:]
        
        new_genes = [b + scale * (p1 - p2) for b, p1, p2 in zip(base, parameter1, parameter2)]
        
        yield type(base)(new_genes, base)

config = {
    'landscape': { 'class': real.Rosenbrock },
    'system': {
        'definition': r'''
            FROM random_real(length=2,lowest=-2.0,highest=2.0) SELECT (size) population
            YIELD population
            
            BEGIN generation
                targets = population
                
                # Stochastic Universal Sampling for bases
                FROM population SELECT (size) bases USING fitness_sus(mu=size)
                
                # Ensure r0 != r1 != r2, but any may equal i
                JOIN bases, population, population INTO mutators USING random_tuples(distinct=True)
                
                FROM mutators SELECT mutants USING mutate_DE(scale=F)
                
                JOIN targets, mutants INTO target_mutant_pairs USING tuples
                FROM target_mutant_pairs SELECT trials USING crossover_tuple(per_gene_rate=CR)
                
                JOIN targets, trials INTO targets_trial_pairs USING tuples
                FROM targets_trial_pairs SELECT population USING best_of_tuple
                
                YIELD population
            END generation''',
        'size': 15,
        'F': 0.8,
        'CR': 0.8,
    },
    'monitor': {
        'report': 'brief+local+local_unique+time',
        'summary': 'status+brief+best_phenome',
        'limits': {
            'generations': 1000,
            'fitness': 1.0e-6,
        }
    },
}

pathbase = 'results/DERosenbrock_00'
import os.path
i = 0
while os.path.exists(pathbase):
    i += 1
    pathbase = 'results/DERosenbrock_%02d' % i

settings = ''
settings += 'pathbase="%s";' % pathbase
settings += 'csv=True;low_priority=True;quiet=True'

def batch():
    for F in (0.2, 0.8, 1.2, 1.8):
        for _ in xrange(1000):
            yield (["F", "F%0.1f" % F], "DERosenbrock+noseed", { "system": { "F": F, "CR": 0.8 } }, None, None)
    for CR in (0.0, 0.2, 0.5, 0.8, 1.0):
        for _ in xrange(1000):
            yield (["CR", "CR%0.1f" % CR], "DERosenbrock+noseed", { "system": { "F": 0.8, "CR": CR } }, None, None)
