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

from math import sqrt
from sys import maxint
from esec import esdl_eval
from esec.context import rand
from esec.fitness import Fitness
from esec.species.tgp import InstructionWithState, DecisionInstructionWithState, ListInstruction
from esec.landscape.tgp import TGPFitness

class SantaFeState(object):
    '''This is passed to all the instructions in a GP program, allowing
    the position of the ant to be persisted and updated through a single
    execution.
    '''
    
    map = [ " XXX                            ",
            "   X                            ",
            "   X                    .XXX..  ",
            "   X                    X    X  ",
            "   X                    X    X  ",
            "   XXXX.XXXXX       .XX..    .  ",
            "            X       .        X  ",
            "            X       X        .  ",
            "            X       X        .  ",
            "            X       X        X  ",
            "            .       X        .  ",
            "            X       .        .  ",
            "            X       .        X  ",
            "            X       X        .  ",
            "            X       X  ...XXX.  ",
            "            .   .X...  X        ",
            "            .   .      .        ",
            "            X   .      .        ",
            "            X   X      .X...    ",
            "            X   X          X    ",
            "            X   X          .    ",
            "            X   X          .    ",
            "            X   .      ...X.    ",
            "            X   .      X        ",
            " ..XX..XXXXX.   X               ",
            " X              X               ",
            " X              X               ",
            " X     .XXXXXXX..               ",
            " X     X                        ",
            " .     X                        ",
            " .XXXX..                        ",
            "                                " ]
    stone_count = sum(sum(c == 'X' for c in s) for s in map)
    assert stone_count == 89, "Santa Fe ant trail should have 89 stones."
    
    def __init__(self):
        self.pos = (0, 0)
        '''The current position of the ant.'''
        self.face = (1, 0)   # east, new_pos = pos + face
        '''The direction the ant is facing. This is designed such that
        `pos` can be updated as such::
        
            pos = (pos[0] + face[0], pos[1] + face[1])
        '''
        self.collected = set()
        '''The stones that have been collected so far.'''
    
    @property
    def _looking(self):
        '''Returns the coordinates of the grid cell the ant is facing.
        '''
        return (self.pos[0] + self.face[0], self.pos[1] + self.face[1])
    
    def _is_stone(self, pos):
        '''Returns ``True`` if `pos` is a stone; otherwise, ``False``.
        If `pos` is outside the bounds of the map, ``False`` is
        returned.
        '''
        return (0 <= pos[1] < len(self.map) and 
                0 <= pos[0] < len(self.map[0]) and
                self.map[pos[0]][pos[1]] == 'X')
    
    def if_sensor(self):
        '''Returns ``True`` if the ant is facing a stone.'''
        return self._is_stone(self._looking) and self._looking not in self.collected
    
    turn_right_map = {
        (1, 0) : (0, 1),
        (0, 1) : (-1, 0),
        (-1, 0): (0, -1),
        (0, -1): (1, 0)
    }
    '''A map from current `face` to the value of `face` after turning
    to the right.
    '''
    def turn_right(self):
        '''Turns the ant to its right.'''
        self.face = self.turn_right_map.get(self.face, (0, 1))
    
    turn_left_map = {
        (1, 0) : (0, -1),
        (0, -1) : (-1, 0),
        (-1, 0): (0, 1),
        (0, 1): (1, 0)
    }
    '''A map from current `face` to the value of `face` after turning
    to the left.
    '''
    def turn_left(self):
        '''Turns the ant to its left.'''
        self.face = self.turn_left_map.get(self.face, (0, 1))
    
    def advance(self):
        '''Advances the ant to the cell it is facing. If a stone is at
        that cell, it is collected.
        '''
        if self.if_sensor():
            self.collected.add(self._looking)
        self.pos = self._looking

# Define an evaluator using @edsl_eval to make it available in the
# system below.
@esdl_eval
def santa_fe_trail(indiv):
    '''Evaluates the
    '''
    state = SantaFeState()
    
    time_limit = 400
    for _ in xrange(time_limit):
        indiv.evaluate(indiv, state)
        if len(state.collected) == state.stone_count:
            break
    
    score = len(state.collected)
    
    return TGPFitness([score, len(indiv[0])])

# Define the instruction set
instructions = [
    InstructionWithState(lambda state: state.advance(), param_count=0, name='ADVANCE'),
    InstructionWithState(lambda state: state.turn_left(), param_count=0, name='TURN-L'),
    InstructionWithState(lambda state: state.turn_right(), param_count=0, name='TURN-R'),
    DecisionInstructionWithState(lambda state: 1 if state.if_sensor() else 2, param_count=2, name='IF-SENSOR'),
    ListInstruction(param_count=2, name='PROGN2'),
    ListInstruction(param_count=3, name='PROGN3'),
]

config = {
    'system': { 
        'instructions': instructions,
        'definition': r'''
            FROM random_tgp(instructions, terminals=0, deepest=4) SELECT (size) population
            EVAL population USING santa_fe_trail
            YIELD population

            BEGIN generation
                FROM population \
                    SELECT (0.9*size) to_cross, (0.02*size) to_mutate, (size) to_reproduce \
                    USING fitness_proportional
                
                FROM to_cross SELECT offspring1 USING crossover_one(deepest_result, terminal_prob=0.1)
                FROM to_mutate SELECT offspring2 USING mutate_random(deepest_result)
                
                FROM offspring1, offspring2, to_reproduce SELECT (size) population
                
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
            'fitness': TGPFitness([89, 7]),
        }
    },
}

settings = 'csv=False;low_priority=True;quiet=True;'
def batch():
    for i in xrange(0, 500):
        yield { 'config': config, 'settings': "random_seed=%d" % i }
