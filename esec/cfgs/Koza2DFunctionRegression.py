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
from esec import esdl_eval
from esec.context import rand
from esec.species.tgp import Instruction, ListInstruction
from esec.landscape.tgp import TGPFitness

# ======================================================================

# Specify the test expression here
def test_expression(x):
    return (
        x**2 + x,
        x - 4
    )

# Define an evaluator using @edsl_eval.
@esdl_eval
def symbolic_regression(indiv):
    error = 0.0
    n = 20
    for _ in xrange(n):
        x = rand.random()
        expected_1, expected_2 = test_expression(x)
        actual_1, actual_2 = indiv.evaluate(indiv, terminals=[x])
        error += (expected_1 - actual_1) ** 2 + (expected_2 - actual_2) ** 2
    score = -sqrt(error / n)
    
    return TGPFitness([score, len(indiv.root_program)])

@symbolic_regression.legal
def symbolic_regression(indiv):
    # Programs are only legal if they don't have X_Y anywhere except at
    # the root. The fixed_root property will ensure that every
    # individual starts with X_Y.
    return all(not isinstance(i, ListInstruction) for i in indiv.root_program[1:])


# Define the instruction set using esec.species.tgp.Instruction
instructions = [
    ListInstruction(param_count=2, name='X_Y'),
    Instruction(lambda a, b: a+b, param_count=2, name='+'),
    Instruction(lambda a, b: a-b, param_count=2, name='-'),
    Instruction(lambda a, b: a*b, param_count=2, name='*'),
    Instruction(lambda a, b: (a/b) if b else 0.0, param_count=2, name='/'),
]

config = {
    'landscape': symbolic_regression,
    'system': { 
        'instructions': instructions,
        'definition': r'''
            FROM random_tgp(instructions, terminals=1, deepest=4, \
                            lowest_int_constant=0, highest_int_constant=5, \
                            fixed_root) SELECT (size) population \
                            USING legal
            YIELD population

            BEGIN generation
                FROM population SELECT (size) to_reproduce \
                    USING fitness_proportional
                
                FROM population SELECT (0.9*size) offspring1 \
                    USING fitness_proportional, \
                          crossover_one(deepest_result, terminal_prob=0.1), \
                          legal
                
                FROM population SELECT (0.02*size) offspring2 \
                    USING fitness_proportional, \
                          mutate_random(deepest_result), \
                          legal
                
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
            'fitness': TGPFitness([-0.1, 0]),
        }
    },
}

settings = 'csv=False;low_priority=True;quiet=True;'
def batch():
    for i in xrange(0, 500):
        yield { 'config': config, 'settings': "random_seed=%d" % i }
