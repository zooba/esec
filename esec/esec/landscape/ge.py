#pylint: disable=C0103, C0302, R0201
# Disable: short variable names, too many lines, method could be a function

'''Grammatical Evolution (GE) problem landscapes.

The `GE` base class inherits from `esec.landscape.Landscape` for some
nice assistive magic. See there for details if you wish to write your
own new functions.

'''

from math import sqrt
from esec.landscape import Landscape

class GE(Landscape):
    '''Abstract GE fitness landscape
    '''
    ltype = 'GE' # subclasses shouldn't change this
    ltype_name = 'Grammatical Evolution'
    size_equals_parameters = False
    
    # this is universal - should not be changed by subclasses
    syntax = {
        'terminals': int,                       # set by the landscape
        
        'size_penalty_square_factor': float,    # penalty factors to
        'size_penalty_linear_factor': float,    # hurt large programs
    }
    
    # subclasses should set default to overlay their changes on to this
    default = {
        'size': { 'min': 1, 'max': 50 },
        'size_penalty_square_factor': 0.0,
        'size_penalty_linear_factor': 0.0,
    }
    
    test_key = ( )
    test_cfg = ( )
    
    def __init__(self, cfg=None, **other_cfg):
        # call parent cfg magic, validate/strict test syntax/defaults/cfg
        super(GE, self).__init__(cfg, **other_cfg)
        
        # set the params using the init/bound values
        self.terminals = self.cfg.terminals
        
        self.size_penalty_square_factor = self.cfg.size_penalty_square_factor
        self.size_penalty_linear_factor = self.cfg.size_penalty_linear_factor
    
    
    def _size_penalty(self, indiv):
        '''Calculate the penalty value based on the size of the program.
        
        Returns d**2 * size_penalty_square_factor + d *
        size_penalty_linear_factor where d is the number of values in
        the genome, regardless of how many are used.
        
        This function is provided as a helper to landscape
        implementations. It is not called automatically.
        '''
        i = len(indiv)
        return i*i*self.size_penalty_square_factor + i*self.size_penalty_linear_factor
    
    def legal(self, indiv):
        '''Check to see if an individual is legal.'''
        return indiv.Eval is not None


#=======================================================================
class Multiplexer(GE):
    '''N-address bit multiplexer
    
    '''
    
    lname = 'Boolean multiplexer'
    maximise = True
    
    complex_rules = {
        '*': [ '"def Eval(T,V):" NEWLINE INC_INDENT Body Return DEC_INDENT' ],
        'Body': [ 'INDENT Line NEWLINE',] + ['INDENT Line NEWLINE Body'],
        'Line': [ 'Variable "=" Expr',
                  '"if " Expr ":" NEWLINE INC_INDENT Body DEC_INDENT' ],
        'Return': [ 'INDENT "return " Variable' ],
        'Variable': [ '"V[%i]"' % i for i in xrange(3) ],
        'Expr': [ 'Source', '"(" Expr BinaryOp Expr ")"', '"(" UnaryOp Expr ")"' ],
        'Source': [ 'TERMINAL', 'Variable' ],
        'UnaryOp': [ '" not "' ],
        'BinaryOp': [ '" and "', '" or "', '" ^ "' ],
    }
    '''A set of rules producing complex programs suitable for this
    landscape.
    '''
    
    simple_rules = {
        '*': [ '"def Eval(T,V): return " Expr' ],
        'Expr': [ 'TERMINAL', '"(" Expr BinaryOp Expr ")"', '"(" UnaryOp Expr ")"',
                  '"(" Expr " if " Expr " else " Expr ")"' ],
        'UnaryOp': [ '"not "' ],
        'BinaryOp': [ '" and "', '" or "', '" ^ "' ],
    }
    '''A set of rules producing simple programs suitable for this
    landscape.
    '''
    
    rules = simple_rules
    '''The default set of rules recommended for this landscape.'''
    
    default = {
        'parameters': 3,
        'terminals': 0, # will be set later, based on parameters
    }
    
    def __init__(self, cfg=None, **other_cfg):
        super(Multiplexer, self).__init__(cfg, **other_cfg)
        
        self.bits = self.cfg.parameters
        self.inputs = 2 ** self.bits
        self.terminals = self.cfg.terminals = self.bits + self.inputs
        
        def _eval(inputs):
            '''Returns the value of the input selected by
            `inputs```[:bits]``.
            '''
            addr = 0
            for i in xrange(self.bits): addr = (addr + addr) | inputs[i]
            return inputs[addr + self.bits]
        
        self.test_cases = []
        for i in xrange(2**self.terminals):
            case = [(True if i & (1 << d) else False) for d in xrange(self.terminals)]
            self.test_cases += [(case, _eval(case))]
    
    def _eval(self, indiv):
        '''Evaluate the set of test cases'''
        fitness = 0
        Eval = indiv.Eval       #pylint: disable=C0103
        
        if Eval is None:
            return -1
        
        for case in self.test_cases:
            result = Eval(case[0], [0] * 10)
            if result is None: return 0
            fitness += 1 if (result == case[1]) else 0
        
        if len(indiv) <= 3: fitness = 0
        if fitness < len(self.test_cases): fitness -= self._size_penalty(indiv)
        
        return fitness



#=======================================================================
class SymbolicRegression(GE):
    '''Symbolic regression of an arbitrary expression.
    
    The default expression is X + X^2 + X^3 + X^4.
    
    '''
    
    lname = 'Symbolic Regression'
    maximise = False
    
    defines = '''import math
class F(float):
    def __add__(self, v): return F(float.__add__(self, v))
    def __sub__(self, v): return F(float.__sub__(self, v))
    def __mul__(self, v): return F(float.__mul__(self, v))
    def __div__(self, v): return F(0 if not v else float.__div__(self, v))
    def __rdiv__(self, v): return F(0 if not self else float.__rdiv__(self, v))

def sin(x): return F(math.sin(x))
def cos(x): return F(math.cos(x))
def exp(x): return F(math.exp(x) if abs(x) <= 709.0 else 0)
def log(x): return F(0 if not x else math.log(abs(x)))
F1 = F(1.0)
'''
    '''The required set of defines for this landscape when using
    `rules`.
    '''
    
    rules = {
        '*': [ '"def Eval(uX): X=F(uX); " Return' ],
        'Return': [ '"return " Expr' ],
        'Expr': [ 'Expr Op Expr', '"(" Expr Op Expr ")"', 'PreOp "(" Expr ")"', 'Variable' ],
        'Op': [ '"+"', '"-"', '"/"', '"*"' ],
        'PreOp': [ '"sin"', '"cos"', '"exp"', '"log"' ],
        'Variable': [ '"X"', '"F1"' ],
    }
    '''The default set of rules recommended for this landscape.'''
    
    syntax = {
        'expr?': str,
        'data?': '*',
    }
    
    default = {
        'parameters': 0,
        'terminals': 1,
        'expr': 'X**4+X**3+X**2+X',
    }
    
    strict = { 'parameters': 0, 'terminals': 1 }
    
    def __init__(self, cfg=None, **other_cfg):
        super(SymbolicRegression, self).__init__(cfg, **other_cfg)
        
        self.parameters = self.cfg.parameters
        self.terminals = 1
        
        math = __import__("math")
        expr = self.cfg.expr
        self.test_cases = []
        if self.cfg.data:
            self.test_cases.extend(self.cfg.data)
        else:
            rnd = self.rand.random
            for _ in xrange(20):
                x = rnd() * 2 - 1
                y = eval(expr, {'math': math, 'x': x, 'X': x})
                self.test_cases += [(x, y)]
    
    def _eval(self, indiv):
        '''Evaluate the set of test cases'''
        fitness = 0
        Eval = indiv.Eval       #pylint: disable=C0103
        
        inf = float('inf')
        if Eval is None: return inf
        
        for case in self.test_cases:
            try:
                result = Eval(case[0])
                if result is None: return inf
                fitness += (result - case[1]) ** 2
            except KeyboardInterrupt:
                raise
            except OverflowError:
                return inf
            except ValueError:
                return inf
        
        fitness += self._size_penalty(indiv)
        
        # Not worth reporting the fitness above this value
        if fitness > 1.0e10: fitness = inf
        
        return sqrt(fitness)

