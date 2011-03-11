#   Copyright 2010-2011 Clinton Woodward and Steve Dower
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

# This example is very similar to KozaSymbolicRegression, except that
# this one is completely self-contained with regards to the evaluator
# and instruction set.

from math import sqrt
from sys import maxint
from esec import esdl_eval
from esec.context import rand
from esec.fitness import Fitness
from esec.species.tgp import Instruction

# ======================================================================

# Make a class for TGP fitnesses (score and cost) with special
# comparison.
# Alternatively::
#
#     from esec.landscape.tgp import TGPFitness
#
class TGPFitness(Fitness):
    '''A TGP specific fitness class that include both a score (to be
    maximised) and a size (to be minimised).
    '''
    types = [float, int]
    defaults = [float('-inf'), maxint]
    
    def should_terminate(self, criteria):
        if hasattr(criteria, 'values'):
            return (self.values[0] >= criteria.values[0] and
                    self.values[1] <= criteria.values[1])
        elif isinstance(criteria, EmptyFitness) or criteria is None:
            return False
        else:
            return self.values[0] >= criteria
    
    def __gt__(self, other):
        # Handle incomparable types
        if not isinstance(other, Fitness): return True
        # self is more fit than other if the score [0] is higher
        if self.values[0] > other.values[0]: return True
        if self.values[0] < other.values[0]: return False
        # if scores are identical, uses cost
        if self.values[1] < other.values[1]: return True
        return False
    
    def __str__(self):
        if __debug__: self.validate()
        score, cost = self.values
        
        if abs(score) < 100000.0:       score_part = ('% 8.2f' % score)
        elif score <= self.defaults[0]: score_part = '   inf'
        elif score > 0:                 score_part = '   +++'
        else:                           score_part = '   ---'
        
        cost_part = (' (%3d)' % cost) if abs(cost) < 100 else ' (---)'
        return score_part + cost_part

# Specify the test expression here
def test_expression(x):
    return x**4 + x**3 + x**2 + x

# Define an evaluator using @edsl_eval to make it available in the
# system below.
@esdl_eval
def symbolic_regression(indiv):
    error = 0.0
    n = 20
    for _ in xrange(n):
        x = rand.random()
        expected = test_expression(x)
        actual = indiv.evaluate(indiv, terminals=[x])
        error += (expected - actual) ** 2
    score = -sqrt(error / n)
    
    return TGPFitness([score, len(indiv[0])])

# Define the instruction set using esec.species.tgp.Instruction
instructions = [
    Instruction(lambda a, b: a+b, param_count=2, name='+'),
    Instruction(lambda a, b: a-b, param_count=2, name='-'),
    Instruction(lambda a, b: a*b, param_count=2, name='*'),
    Instruction(lambda a, b: (a/b) if b else 0.0, param_count=2, name='/'),
]

config = {
    'system': { 
        'instructions': instructions,
        'definition': r'''
            FROM random_tgp(instructions=instructions, \
                            terminals=1, deepest=4, \
                            ) SELECT (size) population
            EVAL population USING symbolic_regression
            YIELD population

            BEGIN generation
                FROM population \
                    SELECT (0.9*size) to_cross, (0.02*size) to_mutate, (size) to_reproduce \
                    USING fitness_proportional
                
                FROM to_cross SELECT offspring1 USING crossover_one(deepest_result, terminal_prob=0.1)
                FROM to_mutate SELECT offspring2 USING mutate_random(deepest_result)
                
                FROM offspring1, offspring2, to_reproduce SELECT (size) population \
                     USING mutate_edit(per_indiv_rate=0.1)
                
                YIELD population
            END generation
        ''',
        'size': 300,
        'deepest_result': 15,
    },
    'monitor': {
        'report': 'gen+births+best+local+best_length+time_delta',
        'summary': 'status+best+best_length+best_phenome',
        'limits': {
            'iterations': 100,
            'fitness': TGPFitness([-0.1, 7]),
        }
    },
}

settings = 'csv=False;low_priority=True;quiet=True;'
def batch():
    for i in xrange(0, 500):
        yield { 'config': config, 'settings': "random_seed=%d" % i }
