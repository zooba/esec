'''Integer value problem landscapes.

The `Integer` base class inherits from `Landscape` for parameter validation and
support. See `landscape` for details.

.. classtree:: esec.landscape.integer.Integer
   :dir: right
'''

from sys import maxsize
from math import sqrt
from itertools import izip as zip   #pylint: disable=W0622
from esec.landscape import Landscape
from esec.utils import all_equal

# Disable: method could be a function, too many lines
#pylint: disable=R0201,C0302

#==============================================================================
class Integer(Landscape):
    '''Abstract integer-valued parameter fitness landscape
    '''
    ltype = 'IVP' # subclasses shouldn't change this
    
    # This is universal for Integer problems
    syntax = {
        'bounds': {
            'lower?': [tuple, list, int, long, float, str, None],
            'upper?': [tuple, list, int, long, float, str, None],
        },
    }
    
    # Subclasses can set default to overlay their changes on to this
    default = {
        'bounds': { 'lower': 0, 'upper': 255 },
        'size': { 'min': 10, 'max': 10 },
    }
    
    test_key = (('size.exact', int), ('bounds.lower', int), ('bounds.upper', int))
    test_cfg = ('2 0 10',) #n=params #low-bounds #high-bounds
    test_legal = ([0, 0], [5, 5], [10, 10]) # used by tests
    test_illegal = ([-5, 15], [5, -5]) # used by tests
    
    def __init__(self, cfg=None, **other_cfg):
        # call parent cfg magic, validate/strict test syntax/defaults/cfg
        super(Integer, self).__init__(cfg, **other_cfg)
        
        # landscape bounds ([lowest value per gene], [highest value per gene])
        lbd = self.cfg.bounds.lower
        if lbd is None: lbd = -maxsize - 1
        if isinstance(lbd, (int, long)): lbd = [lbd] * self.size.max
        elif isinstance(lbd, (float, str)): lbd = [int(lbd)] * self.size.max
        assert len(lbd) >= self.size.max, 'At least %d lower bound values are required' % self.size.max
        
        ubd = self.cfg.bounds.upper
        if ubd is None: ubd = maxsize
        if isinstance(ubd, (int, long)): ubd = [ubd] * self.size.max
        elif isinstance(ubd, (float, str)): ubd = [int(ubd)] * self.size.max
        assert len(ubd) >= self.size.max, 'At least %d upper bound values are required' % self.size.max
        
        self.bounds = (lbd, ubd)
        '''The range limit on each gene.
        
        The first element of `bounds` is a list containing the inclusive
        lower limit of each gene.
        
        The second element of `bounds` is a list containing the inclusive
        upper limit of each gene.
        
        Use `legal` on a genome to determine whether all genes are in the
        legal range.
        '''
    
    
    def legal(self, indiv):
        '''Check to see if an individual is legal.
        '''
        if not (self.size.min <= len(indiv) <= self.size.max):
            return False
        
        lbd, ubd = self.bounds
        for lower, i, upper in zip(lbd, indiv, ubd):
            if not (lower <= i <= upper):
                return False #immediately - don't wait
        return True
    
    def info(self, level):
        '''Return landscape info for any integer landscape.
        '''
        if self.size.exact:
            result = ["Using %s landscape with %d parameter(s)" % (self.lname, self.size.exact)]
        else:
            result = ["Using %s landscape with [%d, %d) parameter(s)" % (self.lname, self.size.min, self.size.max)]
        if level > 0:
            result.append("with parameter bounds of: ")
            result.extend(self._bounds_info(*self.bounds))
        
        result.extend(super(Integer, self).info(level)[1:])
        return result
    
    
    def _bounds_info(self, lbd, ubd):
        '''Returns bounds (less verbosely if all common)'''
        result = []
        if len(lbd) > 5 and all_equal(lbd) and all_equal(lbd):
            for i in xrange(1, 3):
                result.append(" %3d: %10d  %10d" % (i, lbd[0], ubd[0]))
            result.append("    :    ...         ...    ")
            result.append(" %3d: %10d  %10d" % (len(lbd), lbd[0], ubd[0]))
        else:
            for i, (lower, upper) in enumerate(zip(lbd, ubd)):
                result.append(" %3d: %10d  %10d" % ((i+1), lower, upper))
        return result

#==============================================================================
class Nsum(Integer):
    '''N-dimensional N-sum (integer) landscape
    
    Qualities: maximisation
    '''
    lname = 'N-sum'
    
    test_cfg = ('3 0 1',)
    test_legal = ([0, 0, 0], [1, 1, 1])
    test_illegal = ([-1, -1, -1], [2, 2, 2], [0, 4, 1])
    
    def _eval(self, indiv):
        '''Returns the sum of all values'''
        return sum(indiv)


#==============================================================================
class Nmax(Integer):
    '''N-dimensional N-max (integer) landscape
    
    2D example:
        f(x, y) = -sqrt(x^2 + y^2),
        max at (1, 1) for x=(0, 1)
    
    Qualities: maximisation (up to zero), unimodal
    '''
    lname = 'N-max'
    
    test_cfg = ('10 0 31',)
    test_legal = ([5]*10, [20]*10)
    test_illegal = ([-1]*10, [40]*10)
    
    def _eval(self, indiv):
        '''Negative root-sum-squared difference between each gene and
        its maximum value.'''
        if self.legal(indiv):
            fitness = 0
            for expected, actual in zip(self.bounds[1], indiv):
                tmp = expected - actual
                fitness += tmp * tmp
            return -sqrt(fitness)
        else:
            return -1e10000 # -INF

class Nmin(Integer):
    '''N-dimensional N-min (integer) landscape
    
    2D example:
        f(x, y) = sqrt(x^2 + y^2),
        min at (0, 0) for x=(0, 1)
    
    Qualities: minimisation, unimodal
    '''
    lname = 'N-max'
    maximise = False
    
    test_cfg = ('10 0 31',)
    test_legal = ([5]*10, [20]*10)
    test_illegal = ([-1]*10, [40]*10)
    
    def _eval(self, indiv):
        '''Negative root-sum-squared difference between each gene and
        its maximum value.'''
        if self.legal(indiv):
            fitness = 0
            for expected, actual in zip(self.bounds[0], indiv):
                tmp = expected - actual
                fitness += tmp * tmp
            return sqrt(fitness)
        else:
            return 1e10000 # INF


#==============================================================================
class Nmatch(Integer):
    '''N-dimensional N-match (integer) landscape
    
    Like the Nmax function, however optimum is set to centre of the value
    range. ( ie. "Match" the center value.)
    
    
    2D example:
        f(x, y) = -sqrt((x_avg-x)^2 + (y_avg-y)^2),
    Best:
        f(x, y) = 0 = f(0.5, 0.5), for x, y in range of (0, 1)
    
    Qualities: maximisation (up to zero), unimodal
    '''
    lname = 'N-match'
    
    test_cfg = ('10 0 25',)
    test_legal = ([10]*10, [20]*10)
    test_illegal = ([-1]*10, [30]*10)
    
    
    def __init__(self, cfg=None, **other_cfg):
        super(Nmatch, self).__init__(cfg, **other_cfg)
        # specialised setup - target[i] in middle range for each indiv[i].
        self.target = [(upper-lower)//2 for upper, lower in zip(*self.bounds)]
    
    def _eval(self, indiv):
        '''Like the Nmax function with the optimum set to the range center.
        '''
        fitness = 0
        for expected, actual in zip(self.target, indiv):
            tmp = expected - actual
            fitness += tmp * tmp
        return -sqrt(fitness)


#==============================================================================
class Robbins(Integer):
    '''N-dimensional Robbins (integer) landscape
    
    Qualities:
    '''
    lname = 'Robbins'
    
    test_cfg = ('10 -5 5',)
    test_legal = ([0]*10, [5]*10, [-5]*10)
    test_illegal = ([-6]*10, [6]*10)
    
    def _eval(self, indiv):
        '''Map a binary list to an integer value.
        '''
        fitness = 0
        for value in indiv:
            # integer fitness, shift left by 1. eg (256 << 1) == 512
            # genome eval((0, 0, 1, 0, 1, 1) = 8+0+2+1 = 11)
            fitness = (fitness << 1) + value
        return fitness

