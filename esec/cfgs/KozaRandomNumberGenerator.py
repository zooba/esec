#   Copyright 2011 Luke Horvat
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

from math import log
from esec import esdl_eval
from esec.species.tgp import Instruction
from esec.landscape.tgp import TGPFitness

k = 2        # only produce random numbers that are binary
nMax = 7     # generate random numbers of length 1 to 7 bits
jMax = 16384 # the amount of random numbers of length h
             # (h = the current value of n) to generate. an equal
             # occurrence of random numbers is desired.
maxEntropy = nMax * (nMax + 1) / 2

@esdl_eval
def random_number_generation(indiv):
    rawTotalEntropy = 0
    for h in xrange(1, nMax + 1):
        occurrences = dict()
        for j in xrange(1, jMax + 1):
            bits = ""
            # generate a number of length h bits, each bit generated
            # using the individual's program
            for bit in range (0, h):
                # execute the individual's program (consisting of some
                # assortment of functions/instructions and terminals).
                # The program will generate some (hopefully) random
                # number. j, 0, 1, 2, and 3 are terminals.
                result = indiv.evaluate(indiv, terminals=[j, 0, 1, 2, 3])
                bits += "1" if result > 0 else "0"
            occurrences[bits] = occurrences[bits] + 1 if bits in occurrences else 1
        
        # loop through the occurrences of each number and calculate the
        # probability of each
        for occurrence in occurrences.values():
            probability = float(occurrence) / jMax
            # add the current entropy to the total raw entropy
            rawTotalEntropy -= probability * log(probability, k) if probability else 0
    
    return TGPFitness([rawTotalEntropy, len(indiv[0])])

instructions = [
    Instruction(lambda a, b: a+b, param_count=2, name='+'),
    Instruction(lambda a, b: a-b, param_count=2, name='-'),
    Instruction(lambda a, b: a*b, param_count=2, name='*'),
    Instruction(lambda a, b: a//b if b else 0, param_count=2, name='QUOT%'),  #integer division
    Instruction(lambda a, b: a%b if b else 0, param_count=2, name='MOD%'),
]

config = {
    'landscape': random_number_generation,
    'system': { 
        'instructions': instructions,
        'definition': r'''
            FROM random_tgp(instructions=instructions, terminals=5, deepest=4) SELECT (size) population
            YIELD population

            BEGIN generation
                FROM population \
                    SELECT (0.9*size) to_cross, (0.0*size) to_mutate, (0.1*size) to_reproduce \
                    USING fitness_proportional
                
                FROM to_cross SELECT offspring1 USING crossover_one(deepest_result, terminal_prob=0.1)
                FROM to_mutate SELECT offspring2 USING mutate_random(deepest_result)
                
                FROM offspring1, offspring2, to_reproduce SELECT (size) population
                
                YIELD population
            END generation
        ''',
        'size': 500,
        'deepest_result': 17,
    },
    'monitor': {
        'report': 'gen+births+best+local+best_length+time_delta',
        'summary': 'status+best+best_length+best_phenome',
        'limits': {
            'generations': 50,
            'fitness': TGPFitness([maxEntropy - 0.2, 0]),
        }
    },
}

settings = 'csv=True;low_priority=True;quiet=True;'
def batch():
    for i in xrange(0, 10):
        yield { 'config': config, 'settings': "random_seed=%d" % i }
