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
from esec.species.tgp import Instruction, InstructionWithState
from esec.landscape.tgp import TGPFitness

class DNASequenceIterator:
    def __init__(self, sequence):
        self.sequence = sequence
        self.currentIndex = -1
    
    def next(self):
        self.currentIndex += 1
        return self.current_char()
    
    def has_next(self):
        return self.currentIndex < len(self.sequence) - 1
    
    def current_char(self):
        return self.sequence[self.currentIndex]

def hamming_distance(s1, s2):
    assert len(s1) == len(s2)
    return sum(ch1 != ch2 for ch1, ch2 in zip(s1, s2))

# define the DNA sequence and the best expected result (each character
# in the expected result is Boolean; 1 = True, 0 = False)
sequence =           "CAAAGTTTCTGTCAACGTAAGCTAATTGCCAACTTATCCCATGAACTTTAACAACGGTAAACTTCCAGCATGCCAATGCTGTGTCATGCTAGCTAGTAATCGATCGGTCATCCTTAGCTTAGCTAACGCTGGGCACTTTAACTTAGGTACGCATCGACCGGTAAGTCCAATGCCGGGAAACGTTGTAGCTACTTCAAACTTTTTGAAGTCCAGATCGAACCCGATTGAGCGGGGTTGCGGTAAAATTCTGGTCTTTTTAAGCACAAGCTTGCCTTTTTAAAGCTTTAGTCCCTGAACTTGATCCGTAACGTAGTTCCGAAAAAAGCTAGGCGATCGCCCCTCGCGATTGCAATTTGTATTGCGCTATCCCGATTTCGCTAAAGTCCGAAGGTCTTTCGATTCGGAAACTCGGCTAGCTAGATAGATACCAATTTAGATCCGATTCGATCGCCTAGATCAGAAAAACCGATCGTTAAGCTTTGAAATCGGAGCTGCTCGCAAGTTTAATGCTGGCTTCAACTTACCCCTGAATCGTAGATTGCATTTTTCGAAGCGCGATAATATAAAATTGCTAGATCGCTAGCTATATCGATCGGCTGATCGTAACATGCAAGTTTAGTAGCTGCRTTAAAGCCTGTACCCGTTTGATCGAACTTTAGTACGTAGCGGGGTACGATGTAGCAGCTGTCAGCTAGCCTTGATCGATGCAAGTCAGTAGCCCTTAGTTTCGGAAACTTAGCTAGCGCTGTGCCGTGCTCTGATCGTACCCGTAAGCCTGTCAGTGCGAAATGCCTTAAAAAGTTATGTCCAGGGTCCAGGACAAGTACGTAAATAAGTCCAATGTTGCAATGCTGCAAATTTGAATTTGTCCCTGACCCCGTAGCTCGTCGATCGATCGATCGTAAGCATGCATGCGTAGATATCGATTAAAGTTGCTAGCCGGATGCTAGGGTCCAGTCCCTGAACGTCAGTCAATCCCGCTAAATGAAATTCAACTCGA"
bestResultSequence = "0011111000000000000000000000001111100000000000000000000000011111000000000000000000000000000000000000000000000000000000000000000000000000000111110000000000000000000000000000000000000000000000000000111110000000000000000000000000000000000000000011111000000000000000000000000000000000000000000000001111100000000000000000000000000000000000000000000000000011111000000000000000000000000000000000000000000000000000000000000000000000000001111100000000000000000000000000000000000000000000000000000000000000000111110000000000000111110000000000000000000000000000000000000000000111110000000000000000000000000000000000000000011111000000000000000000000000000000000001111100000000000000000000000000000000000000000000000000000000000000000000000000001111100000000000000000000000000000000000000000000000000000000000001111100000000000000000000000000000000000000000000000000001111100111110000000000000000000000000000000000000000000000000000000000000011111000000000000000000000000000000000000000000000000000001111100000000"
maxScore = len(sequence)

@esdl_eval
def grammar_induction(indiv):
    dnaIterator = DNASequenceIterator(sequence)
    resultSequence = ""
    while (dnaIterator.has_next()):
        dnaIterator.next() #iterate to the next un-examined character
        startingIndex = dnaIterator.currentIndex
        
        # call the individual's program. The amount of characters that
        # will be examined with this single call will depend on how many
        # MHG() calls there are in the program.
        result = indiv.evaluate(indiv, dnaIterator)
        
        # if the sub-sequence was determined to be an exon (i.e. result
        # = true), add "1" to the result sequence for every character
        # that was examined
        if result:
            for i in range(startingIndex, dnaIterator.currentIndex + 1):
                resultSequence += "1"
        else:
            resultSequence += "0"
            dnaIterator.currentIndex = startingIndex
    
    # compare characters in the result sequence to the best expected
    # result sequence and calculate a score based on the difference
    score = maxScore - hamming_distance(resultSequence, bestResultSequence)
        
    return TGPFitness([score, len(indiv[0])])

def MHG(dnaIterator):
    if (dnaIterator.has_next()):
        dnaIterator.next() #increment the current sequence position
    
    return True

instructions = [
    InstructionWithState(lambda dnaIterator: dnaIterator.current_char() == "A", param_count=0, name='AIF'),
    InstructionWithState(lambda dnaIterator: dnaIterator.current_char() == "C", param_count=0, name='CIF'),
    InstructionWithState(lambda dnaIterator: dnaIterator.current_char() == "G", param_count=0, name='GIF'),
    InstructionWithState(lambda dnaIterator: dnaIterator.current_char() == "T", param_count=0, name='TIF'),
    InstructionWithState(lambda dnaIterator: MHG(dnaIterator), param_count=0, name='MHG'),
    Instruction(lambda a, b: a and b, 2, 'AND'),
    Instruction(lambda a, b: a or b, 2, 'OR'),
    Instruction(lambda a: not a, 1, 'NOT')
]

config = {
    'landscape': grammar_induction,
    'system': { 
        'instructions': instructions,
        'definition': r'''
            FROM random_tgp(instructions=instructions, terminals=0, deepest=4) SELECT (size) population
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
    for i in xrange(0, 12):
        yield { 'config': config, 'settings': "random_seed=%d" % i }
