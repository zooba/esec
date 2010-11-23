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

'''A Differential Evolution plugin.

This plugin provides a Differential Evolution system definition.
'''

from esec import esdl_func
from itertools import izip as zip

@esdl_func
def mutate_DE(_source, scale):
    '''A generator that yields one mutated Individual for every
    JoinedIndividual passed in source.
    '''
    def _combine(v1, p1, p2, low, high):
        result = v1 + scale * (p1 - p2)
        result = result if result < high else high
        result = result if result > low else low
        return result
    
    for joined_individual in _source:
        base, parameter1, parameter2 = joined_individual[:]
        yield type(base)([_combine(b, p1, p2, l, h) for
                          b, p1, p2, l, h in zip(base, parameter1, parameter2, base.lower_bounds, base.upper_bounds)],
                         base)

DE_DEF = r'''
FROM random_real(length=config.landscape.size.exact, \
                 lowest=config.landscape.lower_bounds,highest=config.landscape.upper_bounds) \
        SELECT (size) population
YIELD population

BEGIN GENERATION
    targets = population
    
    # Stochastic Universal Sampling for bases
    FROM population SELECT (size) bases USING fitness_sus(mu=size)
    
    # Ensure r0 != r1 != r2, but any may equal i
    JOIN bases, population, population INTO mutators USING random_tuples(distinct=True)
    
    FROM mutators SELECT mutants USING mutate_DE(scale=0.1)
    
    JOIN targets, mutants INTO target_mutant_pairs USING tuples
    FROM target_mutant_pairs SELECT trials USING crossover_tuple(per_gene_rate=0.5)
    
    JOIN targets, trials INTO targets_trial_pairs USING tuples
    FROM targets_trial_pairs SELECT population USING best_of_tuple
    
    YIELD population
END GENERATION
'''

defaults = {
    'system': {
        'size': 100,
        'definition': DE_DEF,
    }
}