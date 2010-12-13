#pylint: disable=R0201
# Disable: method could be a function

'''Tree-based Genetic Programming (TGP) problem landscapes.

The `TGP` base class inherits from `esec.landscape.Landscape` for some
nice assistive magic. See there for details if you wish to write your
own new functions.

'''

from esec.landscape import Landscape
from esec.fitness import Fitness
import sys

class TGPFitness(Fitness):
    '''Represents a fitness value for TGP landscapes.'''
    # stage 0 is the score of the solution (higher == better)
    # stage 1 is the cost (lower == better)
    types = [ float, long ]
    defaults = [ float('-inf'), sys.maxsize ]
    
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
        assert len(self.values) == 2
        score, cost = self.values
        if abs(score) < 100000.0:
            score_part = ('% 8.2f' % score)
        elif score > 0:
            score_part = '   +++'
        elif score <= self.defaults[0]:
            score_part = '   inf'
        else:
            score_part = '   ---'
        cost_part = (' (%3d)' % cost) if abs(cost) < 100 else ' (---)'
        return score_part + cost_part


class TGP(Landscape):
    '''Abstract TGP fitness landscape'''
    ltype = 'TGP' # subclasses shouldn't change this
    size_equals_parameters = False
    
    # this is universal - should not be changed by subclasses
    syntax = {
        'parameters': int,          # landscape specific
        'instruction_set?': list,   # optional instruction set name(s)
    }
    # subclasses should set default to overlay their changes on to this
    default = {
        'size': { 'min': 1, 'max': 50 }
    }
    strict = { 'size.min': 1 }
    
    test_key = ( )
    test_cfg = ( )
    
    def __init__(self, cfg=None, **other_cfg):
        # call parent cfg magic, validate/strict test syntax/defaults/cfg
        super(TGP, self).__init__(cfg, **other_cfg)
        
        # set the params using the init/bound values
        self.adfs = self.cfg.adfs
        self.instruction_set = self.cfg.instruction_set
    
    
    def _size_penalty(self, indiv):
        '''Calculate the penalty value based on the size of the program.
        
        Returns the sum of the node count of the main program tree and
        any ADFs.
        
        This function is provided as a helper to landscape
        implementations. It is not called automatically.
        '''
        return sum((len(adf) for adf in indiv))
    
    def legal(self, indiv):     #pylint: disable=W0613
        '''Check to see if an individual is legal.'''
        # TGP individuals are always legal by design, though certain
        # problems may override this method and apply extra criteria.
        return True


#=======================================================================
class Multiplexer(TGP):
    '''N-address bit multiplexer.'''
    
    lname = 'Boolean multiplexer'
    
    default = {
        'parameters': 3,
        'instruction_set': ['boolean'],
    }
    
    def __init__(self, cfg=None, **other_cfg):
        super(Multiplexer, self).__init__(cfg, **other_cfg)
        
        self.bits = self.cfg.parameters
        self.inputs = 2 ** self.bits
        self.terminals = self.bits + self.inputs
        
        
        def _eval(inputs):
            '''Returns the value of the input selected by
            `inputs```[:bits]``.
            '''
            addr = 0
            for i in xrange(self.bits): addr = (addr + addr) | inputs[i]
            return inputs[addr + self.bits]
        
        self.test_cases = []
        for i in xrange(2**self.terminals):
            case = [(1 if i & (1 << d) else 0) for d in xrange(self.terminals)]
            self.test_cases += [(case, _eval(case))]
    
    def _eval(self, indiv):
        '''Evaluate the set of test cases'''
        assert self.instruction_set and indiv.instruction_set in self.instruction_set, \
            ' or '.join(self.instruction_set).capitalize() + " instructions expected."
        assert indiv.terminals >= self.terminals, "At least %d terminals required" % self.terminals
        fitness = 0
        for case in self.test_cases:
            result = indiv.evaluate(indiv, case[0])
            fitness += 1 if (result == case[1]) else 0
        
        cost = self._size_penalty(indiv)
        
        return TGPFitness([fitness, cost])


#=======================================================================
class SymbolicRegression(TGP):
    '''Symbolic regression.'''
    
    lname = 'Symbolic Regression'
    
    syntax = { 'expr': str }
    default = {
        'parameters': 1,
        'instruction_set': ['real', 'integer'],
        'expr': 'X**4 + X**3 + X**2 + X',
    }
    strict = { 'parameters': 1 }
    
    def __init__(self, cfg=None, **other_cfg):
        super(SymbolicRegression, self).__init__(cfg, **other_cfg)
        
        self.terminals = self.cfg.parameters
        
        self.test_cases = []
        math = __import__("math")
        expr = self.cfg.expr
        rnd = self.rand.random
        for _ in xrange(20):
            x = rnd() * 2 - 1
            y = eval(expr, {'math': math, 'x': x, 'X': x})
            self.test_cases += [([x], y)]
    
    
    def _eval(self, indiv):
        '''Evaluate the set of test cases'''
        assert self.instruction_set and indiv.instruction_set in self.instruction_set, \
            ' or '.join(self.instruction_set).capitalize() + " instructions expected."
        assert indiv.terminals >= self.terminals, "At least %d terminals required" % self.terminals
        fitness = 0
        for case in self.test_cases:
            try:
                result = indiv.evaluate(indiv, case[0])
                fitness -= abs(result - case[1])
            except KeyboardInterrupt:
                raise
            except:
                return TGPFitness()
        
        cost = self._size_penalty(indiv)
        
        return TGPFitness([fitness, cost])


