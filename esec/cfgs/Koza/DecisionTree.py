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

from esec import esdl_eval
from esec.species.tgp import Instruction, DecisionInstructionWithState
from esec.landscape.tgp import TGPFitness

#define the weather attributes of a Saturday morning
outlookSunny = "SUNNY"
outlookOvercast = "OVERCAST"
outlookRain = "RAIN"
humidityHigh = "HIGH"
humidityNormal = "NORMAL"
windyTrue = "TRUE"
windyFalse = "FALSE"

#define the state object to store weather attributes
class SaturdayMorning:
    def __init__(self, outlook, humidity, windy):
        self.outlook = outlook
        self.humidity = humidity
        self.windy = windy

    def classification(self):
        if (self.outlook == outlookSunny):
            return 0 if (self.humidity == humidityHigh) else 1
        elif (self.outlook == outlookOvercast):
            return 1
        elif (self.outlook == outlookRain):
            return 0 if (self.windy == windyTrue) else 1

#define the fitness cases
fitnessCases = set()
fitnessCases.add(SaturdayMorning(outlookSunny, humidityHigh, windyTrue,))
fitnessCases.add(SaturdayMorning(outlookSunny, humidityHigh, windyFalse))
fitnessCases.add(SaturdayMorning(outlookSunny, humidityNormal, windyFalse))
fitnessCases.add(SaturdayMorning(outlookSunny, humidityNormal, windyTrue))
fitnessCases.add(SaturdayMorning(outlookOvercast, humidityHigh, windyTrue))
fitnessCases.add(SaturdayMorning(outlookOvercast, humidityHigh, windyFalse))
fitnessCases.add(SaturdayMorning(outlookOvercast, humidityNormal, windyFalse))
fitnessCases.add(SaturdayMorning(outlookOvercast, humidityNormal, windyTrue))
fitnessCases.add(SaturdayMorning(outlookRain, humidityHigh, windyTrue))
fitnessCases.add(SaturdayMorning(outlookRain, humidityHigh, windyFalse))
fitnessCases.add(SaturdayMorning(outlookRain, humidityNormal, windyFalse))
fitnessCases.add(SaturdayMorning(outlookRain, humidityNormal, windyTrue))

@esdl_eval
def decision_tree_induction(indiv):
    score = 0
    for fitnessCase in fitnessCases:
        result = indiv.evaluate(indiv, fitnessCase, terminals=[0, 1])
        score += 1 if result == fitnessCase.classification() else 0
    
    return TGPFitness([score, len(indiv[0])])

# Define the instruction set using esec.species.tgp.Instruction
instructions = [
    # evaluate the 1st, 2nd or 3rd parameter based on the conditions
    DecisionInstructionWithState(lambda state: 1 if state.outlook == outlookSunny else (2 if state.outlook == outlookOvercast else 3), param_count=3, name='OUTLOOK'),
    DecisionInstructionWithState(lambda state: 1 if state.humidity == humidityHigh else 2, param_count=2, name='HUMIDITY'),
    DecisionInstructionWithState(lambda state: 1 if state.windy == windyTrue else 2, param_count=2, name='WINDY'),
    
    # alternatively, the instructions can be defined in this way:
    # return the (evaluated) result of the 1st, 2nd or 3rd parameter
    #InstructionWithState(lambda state, a, b, c: a if state.outlook == outlookSunny else (b if state.outlookOvercast else c), param_count=3, name='OUTLOOK'),
    #InstructionWithState(lambda state, a, b: a if state.humidity == humidityHigh else b, param_count=2, name='HUMIDITY'),
    #InstructionWithState(lambda state, a, b: a if state.windy == windyTrue else b, param_count=2, name='WINDY'),
]

config = {
    'landscape': decision_tree_induction,
    'system': {
        'instructions': instructions,
        'definition': r'''
            FROM random_tgp(instructions=instructions, terminals=2, deepest=4) SELECT (size) population
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
            'fitness': TGPFitness([len(fitnessCases), 0]),
        }
    },
}

settings = 'csv=True;low_priority=True;quiet=True;'
def batch():
    for i in xrange(0, 20):
        yield { 'config': config, 'settings': "random_seed=%d" % i }
