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
from esec.species.tgp import DecisionInstructionWithState
from esec.landscape.tgp import TGPFitness

#class that defines binary nodes
class BNode:
    def __init__(self, payoff=None, leftChildNode=None, rightChildNode=None):
        self.payoff = payoff
        self.leftChildNode = leftChildNode
        self.rightChildNode = rightChildNode
    
    def set_payoff(self, payoff):
        self.payoff = payoff
    
    def get_payoff(self):
        return self.payoff
    
    def set_left_child(self, leftChildNode):
        self.leftChildNode = leftChildNode
        
    def set_right_child(self, rightChildNode):
        self.rightChildNode = rightChildNode
    
    def get_left_child(self):
        return self.leftChildNode
        
    def get_right_child(self):
        return self.rightChildNode
    
    def has_left_child(self):
        return self.leftChildNode != None
    
    def has_right_child(self):
        return self.rightChildNode != None
    
#define the game tree for the 32-outcome discrete game
rootNode = BNode(12, 
                   BNode(12, 
                         BNode(16, 
                               BNode(16, 
                                     BNode(32, 
                                           BNode(32), 
                                           BNode(31)), 
                                     BNode(16, 
                                           BNode(15), 
                                           BNode(16))), 
                               BNode(8, 
                                     BNode(8, 
                                           BNode(7), 
                                           BNode(8)), 
                                     BNode(24, 
                                           BNode(24), 
                                           BNode(23)))), 
                         BNode(12, 
                               BNode(4, 
                                     BNode(4, 
                                           BNode(3), 
                                           BNode(4)), 
                                     BNode(20, 
                                           BNode(20), 
                                           BNode(19))), 
                               BNode(12, 
                                     BNode(28, 
                                           BNode(28), 
                                           BNode(27)), 
                                     BNode(12, 
                                           BNode(11), 
                                           BNode(12))))), 
                   BNode(10,
                         BNode(10, 
                               BNode(2, 
                                     BNode(2, 
                                           BNode(1), 
                                           BNode(2)), 
                                     BNode(18, 
                                           BNode(18), 
                                           BNode(17))), 
                               BNode(10, 
                                     BNode(26, 
                                           BNode(26), 
                                           BNode(25)), 
                                     BNode(10, 
                                           BNode(9), 
                                           BNode(10)))), 
                         BNode(14, 
                               BNode(14, 
                                     BNode(30, 
                                           BNode(30), 
                                           BNode(29)), 
                                     BNode(14, 
                                           BNode(13), 
                                           BNode(14))), 
                               BNode(6, 
                                     BNode(6, 
                                           BNode(5), 
                                           BNode(6)), 
                                     BNode(22, 
                                           BNode(22), 
                                           BNode(21))))))

# define the game state class
class GameMovesHistory:
    def __init__(self, xm1=None, om1=None, xm2=None, om2=None):
        self.xm1 = xm1
        self.om1 = om1
        self.xm2 = xm2
        self.om2 = om2

# define the four fitness cases. the fitness cases cover all the
# possible combinations of O's moves (i.e. L or R for 2 moves)
oMovesList = [ ["L", "L"], ["L", "R"], ["R", "L"], ["R", "R"] ]

# define the max score. for X playing against all of O's possible
# combinations of moves (oMovesList), 88 is the highest payoff sum that
# can be attained. it is the result of 32+16+28+12 (see the game tree
# diagram for a better understanding).
maxScore = 88

@esdl_eval
def minimax_strategy(indiv):
    score = 0
    
    # compute X's first move (can be done prior to the separate fitness
    # cases loop since it does not require information on any of X or
    # O's previous moves)
    xm1 = indiv.evaluate(indiv, GameMovesHistory(), terminals=["L", "R"])
    oNode1 = rootNode.get_left_child() if xm1 == "L" else rootNode.get_right_child()
    
    # for every possible combination of O's first and second moves,
    # compute X's second and third moves and receive the final payoff
    for oMoves in oMovesList:
        om1 = oMoves[0] # get the first move by O
        xNode2 = oNode1.get_left_child() if om1 == "L" else oNode1.get_right_child()
        
        xm2 = indiv.evaluate(indiv, GameMovesHistory(xm1, om1), terminals=["L", "R"]) # get the second move by X
        oNode2 = xNode2.get_left_child() if xm2 == "L" else xNode2.get_right_child()
        
        om2 = oMoves[1] # get the second move by O
        xNode3 = oNode2.get_left_child() if om2 == "L" else oNode2.get_right_child()
        
        xm3 = indiv.evaluate(indiv, GameMovesHistory(xm1, om1, xm2, om2), terminals=["L", "R"]) # get the third move by X
        finalNode = xNode3.get_left_child() if xm3 == "L" else xNode3.get_right_child()
        
        score += finalNode.get_payoff()
    
    return TGPFitness([score, len(indiv[0])])

instructions = [
    DecisionInstructionWithState(lambda movesHistory: 1 if movesHistory.xm1 == None else (2 if movesHistory.xm1 == "L" else 3), param_count=3, name='CXM1'),
    DecisionInstructionWithState(lambda movesHistory: 1 if movesHistory.om1 == None else (2 if movesHistory.om1 == "L" else 3), param_count=3, name='COM1'),
    DecisionInstructionWithState(lambda movesHistory: 1 if movesHistory.xm2 == None else (2 if movesHistory.xm2 == "L" else 3), param_count=3, name='CXM2'),
    DecisionInstructionWithState(lambda movesHistory: 1 if movesHistory.om2 == None else (2 if movesHistory.om2 == "L" else 3), param_count=3, name='COM2'),
]

config = {
    'landscape': minimax_strategy,
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
            'fitness': TGPFitness([maxScore, 0]),
        }
    },
}

settings = 'csv=True;low_priority=True;quiet=True;'
def batch():
    for i in xrange(0, 20):
        yield { 'config': config, 'settings': "random_seed=%d" % i }
