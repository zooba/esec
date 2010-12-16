'''Integer value problem landscapes.

The `Integer` base class inherits from `Landscape` for parameter
validation and support. See `landscape` for details.
'''

from sys import maxsize
from math import sqrt
from itertools import izip
from esec.landscape import Landscape
from esec.utils import all_equal

# Disable: method could be a function, too many lines
#pylint: disable=R0201,C0302

#=======================================================================
class Integer(Landscape):
    '''Abstract integer-valued parameter fitness landscape
    '''
    ltype = 'IVP' # subclasses shouldn't change this
    
    # This is universal for Integer problems
    syntax = {
        'bounds': {
            'lower': [tuple, list, int, long, float, str, None],
            'upper': [tuple, list, int, long, float, str, None],
        },
        # lower_bounds overrules bounds.lower
        'lower_bounds?': [tuple, list, int, long, float, str, None],
        # upper_bounds overrules bounds.upper
        'upper_bounds?': [tuple, list, int, long, float, str, None],
    }
    
    # Subclasses can set default to overlay their changes on to this
    # Note that specifying defaults for lower_bounds or upper_bounds
    # will overrule any settings for bounds.lower or bounds.upper.
    default = {
        'bounds': {
            'lower': 0,
            'upper': 255,
        },
        'size': { 'min': 10, 'max': 10 },
    }
    
    test_key = (('size.exact', int), ('bounds.lower', int), ('bounds.upper', int))
    test_cfg = ('2 0 10',) #n=params #low-bounds #high-bounds
    test_legal = ([0, 0], [5, 5], [10, 10]) # used by tests
    test_illegal = ([-5, 15], [5, -5]) # used by tests
    
    def __init__(self, cfg=None, **other_cfg):
        # call parent cfg magic, validate/strict test syntax/defaults/cfg
        super(Integer, self).__init__(cfg, **other_cfg)
        
        # landscape bounds
        lbd = self.cfg.lower_bounds or self.cfg.bounds.lower
        if lbd is None: lbd = (-maxsize) - 1
        if isinstance(lbd, (int, long)): lbd = [lbd] * self.size.max
        elif isinstance(lbd, (float, str)): lbd = [int(lbd)] * self.size.max
        assert len(lbd) >= self.size.max, 'At least %d lower bound values are required' % self.size.max
        
        ubd = self.cfg.upper_bounds or self.cfg.bounds.upper
        if ubd is None: ubd = maxsize
        if isinstance(ubd, (int, long)): ubd = [ubd] * self.size.max
        elif isinstance(ubd, (float, str)): ubd = [int(ubd)] * self.size.max
        assert len(ubd) >= self.size.max, 'At least %d upper bound values are required' % self.size.max
        
        self.lower_bounds = lbd
        '''The inclusive lower range limit on each gene.
        
        Use `legal` on a genome to determine whether all genes are in
        the legal range.
        '''
        self.upper_bounds = ubd
        '''The inclusive upper range limit on each gene.
        
        Use `legal` on a genome to determine whether all genes are in
        the legal range.
        '''
    
    
    def legal(self, indiv):
        '''Check to see if an individual is legal.'''
        if not (self.size.min <= len(indiv) <= self.size.max):
            return False
        
        for lower, i, upper in izip(self.lower_bounds, indiv, self.upper_bounds):
            if not (lower <= i <= upper):
                return False
        return True
    
    def info(self, level):
        '''Return landscape info for any integer landscape.'''
        if self.size.exact:
            result = ["Using %s landscape with %d parameter(s)" % (self.lname, self.size.exact)]
        else:
            result = ["Using %s landscape with [%d, %d) parameter(s)" % (self.lname, self.size.min, self.size.max)]
        if level > 0:
            result.append("with parameter bounds of: ")
            result.extend(self._bounds_info(self.lower_bounds, self.upper_bounds))
        
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
            for i, (lower, upper) in enumerate(izip(lbd, ubd)):
                result.append(" %3d: %10d  %10d" % ((i+1), lower, upper))
        return result

#=======================================================================
class Nsum(Integer):
    '''n-dimensional summing (N-sum) benchmark landscape.
    
    Qualities: maximisation
    '''
    lname = 'N-sum'
    
    test_cfg = ('3 0 1',)
    test_legal = ([0, 0, 0], [1, 1, 1])
    test_illegal = ([-1, -1, -1], [2, 2, 2], [0, 4, 1])
    
    def _eval(self, indiv):
        '''Returns the sum of all values'''
        return sum(indiv)


#=======================================================================
class Nmax(Integer):
    '''n-dimensional maximum value (N-max) benchmark landscape.
    
    For example, when n = 2 and x is in [0, 1]::
    
        f(x) = sqrt(x_1^2 + x_2^2)
        f_max = 0.0, x = (1, 1)
    
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
            fitness = sum((expected - actual) ** 2 for expected, actual in izip(self.upper_bounds, indiv))
            return sqrt(fitness)
        else:
            return 1e10000 # -INF

class Nmin(Integer):
    '''n-dimensional minimum value (N-min) benchmark landscape.
    
    For example, when n = 2 and x is in [0, 1]::
    
        f(x) = sqrt(x_1^2 + x_2^2)
        f_max = 0.0, x = (0, 0)
    
    Qualities: minimisation, unimodal
    '''
    lname = 'N-min'
    maximise = False
    
    test_cfg = ('10 0 31',)
    test_legal = ([5]*10, [20]*10)
    test_illegal = ([-1]*10, [40]*10)
    
    def _eval(self, indiv):
        '''Root-sum-squared difference between each gene and its minimum
        value.
        '''
        if self.legal(indiv):
            fitness = sum((expected - actual) ** 2 for expected, actual in izip(self.lower_bounds, indiv))
            return sqrt(fitness)
        else:
            return 1e10000 # INF


#=======================================================================
class Nmatch(Integer):
    '''n-dimensional value find (N-match) landscape.
    
    Like the Nmax function, however optimum is set to centre of the
    value range. (ie. "Match" the center value.)
    
    
    For example, when n = 2 and x is in [0, 1]::
    
        f(x) = sqrt(x_1^2 + x_2^2)
        f_max = 0.0, x = (0.5, 0.5)
    
    Qualities: minimisation, unimodal
    '''
    lname = 'N-match'
    maximise = False
    
    test_cfg = ('10 0 25',)
    test_legal = ([10]*10, [20]*10)
    test_illegal = ([-1]*10, [30]*10)
    
    
    def __init__(self, cfg=None, **other_cfg):
        super(Nmatch, self).__init__(cfg, **other_cfg)
        # specialised setup - target[i] in middle range for each indiv[i].
        self.target = [(upper-lower) // 2 + lower for upper, lower in izip(self.lower_bounds, self.upper_bounds)]
    
    def _eval(self, indiv):
        '''Like the Nmax function with the optimum set to the range
        center.
        '''
        if self.legal(indiv):
            fitness = sum((expected - actual) ** 2 for expected, actual in izip(self.target, indiv))
            return sqrt(fitness)
        else:
            return 1e10000 # INF


#=======================================================================
class Robbins(Integer):
    '''N-dimensional Robbins (integer) landscape
    
    Qualities: maximisation (default) or minimisation
    '''
    lname = 'Robbins'
    maximise = True
    
    test_cfg = ('10 -5 5',)
    test_legal = ([0]*10, [5]*10, [-5]*10)
    test_illegal = ([-6]*10, [6]*10)
    
    def _eval(self, indiv):
        '''Map a binary list to an integer value.'''
        fitness = 0
        for value in indiv:
            # integer fitness, shift left by 1. eg (256 << 1) == 512
            # genome eval((0, 0, 1, 0, 1, 1) = 8+0+2+1 = 11)
            fitness = (fitness << 1) + value
        return fitness

