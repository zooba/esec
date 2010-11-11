#pylint: disable=C0103, C0302, R0201
# Disable: short variable names, too many lines, method could be a function

'''Binary valued problem landscapes.

The `Binary` base class inherits from `Landscape` for parameter
validation and support. See `landscape` for details.

Most of these binary landscapes are problem generators.

.. classtree:: esec.landscape.binary.Binary
   :dir: right

'''

from itertools import izip as zip   #pylint: disable=W0622
from esec.landscape import Landscape
from esec.individual import JoinedIndividual

#=======================================================================
def inttobin(n, count=24):
    '''Convert an integer number in a string with count places.
    '''
    return "".join((str(i) for i in inttobinlist(n, count)))

def inttobinlist(n, count=24):
    '''Convert an integer number in a list with count places.
    '''
    return [int((n >> y) & 1) for y in xrange(count - 1, -1, -1)]


#=======================================================================
class Binary(Landscape):
    '''Abstract binary (Boolean) string fitness landscape
    '''
    ltype = 'BVP' # subclasses shouldn't change this
    
    syntax = { }
    default = { }
    
    # default testing is no parameters are needed
    test_key = ()
    test_cfg = () # all should be tested...
    
    def legal(self, indiv):
        '''Check to see if the indiv's are legal for any Binary problem.
        '''
        return all(p in (0, 1) for p in indiv)
    
    def info(self, level):
        '''Return landscape info for any Binary landscape.'''
        result = super(Binary, self).info(level)
        if self.size.exact:
            result[0] += " with %d parameter(s)" % self.size.exact
        else:
            result[0] += " with [%d, %d) parameter(s)" % (self.size.min, self.size.max)
        
        return result

#=======================================================================

class OneMax(Binary):
    '''Simple binary maximisation problem. A classic binary GA domain
    also known as "bit counting" or simply "max".
        
        f(x) = sum(x)
    
    Qualities: maximisation, unconstrained
    '''
    lname = 'Binary OneMax'
    size_equals_parameters = False
    
    syntax = { 'N?': int }
    default = { 'parameters': 4 }
    
    test_key = (('parameters', int),)
    test_cfg = ('4', '10')
    
    def __init__(self, cfg=None, **other_cfg):
        super(OneMax, self).__init__(cfg, **other_cfg)
        self.size.min = self.size.max = self.size.exact = self.cfg.N or self.cfg.parameters
    
    def _eval(self, indiv):
        '''Count the bits.
        '''
        return sum(indiv)


#=======================================================================
class RoyalRoad(Binary):
    '''A discrete non-deceptive unimodal problem space. Essentially,
    maximise the number Q of complete "blocks" of size C each. The
    typical form is minimisation, so that the output becomes zero as all
    blocks are found.
    
    In principle designed to allow GA's using building-block's (BB) to
    find the solution more easily than hill-climbing algorithms, as
    single steps are rewarded less than larger BB size changes. See
    \cite{Mitchell1992}.
        
        Maximisation:  f(x) = sum(blocks(x))*C
        Minimisation:  f(x) = C*N - sum(blocks(x))*C
    
    This is a very simple non-overlapping model. If you are serious
    about investigating building blocks, you will want a better version
    of this evaluator that supports overlapping schema (hierarchical).
    
    If C=3, and Q=4, N=3*4=12, and the following examples apply::
        
        x_1 x_2 x_3 x_4 |  Q(xi)  | f(x)
        ----------------+---------+------
        000 000 000 000 | 0 0 0 0 |   0
        000 111 000 000 | 0 3 0 0 |   3
        000 010 111 000 | 0 0 3 0 |   3
        111 001 100 111 | 3 0 0 3 |   6
        111 111 111 111 | 3 3 3 3 |  12
    
    Qualities: maximisation, multimodal
    '''
    lname = 'Royal Road'
    size_equals_parameters = False
    
    syntax = {
        'Q': int, # number of blocks
        'C': int  # size of each block
    }
    
    test_key = (('Q', int), ('C', int),)
    test_cfg = ('4 3', '10 10')
    
    def __init__(self, cfg=None, **other_cfg):
        super(RoyalRoad, self).__init__(cfg, **other_cfg)
        
        Q = self.Q = self.cfg.Q
        C = self.C = self.cfg.C
        self.size.min = self.size.max = self.size.exact = Q * C
    
    def _eval(self, indiv):
        '''f(x) = sum(blocks(x)) * C'''
        total = 0
        C = self.C
        for i in xrange(0, self.size.exact, C):
            q = indiv[i:i+C] # get each block of C genes
            if sum(q) == C:
                total += C
        return total
    


#=======================================================================
class GoldbergD3B(Binary):
    '''Goldberg's Deceptive 3-bit Function
    
    A deliberately deceptive function for analysis of binary GAs. Also
    known as Goldberg's order-3 minimal deceptive problem.  A binary
    genome must be composed of N * 3 segments, and each segment is
    mapped m() to a value.
        
        f(x) = sum(m(x)),
    
    where the mapping function m() is either a maximisation or
    minimisation set. The maximum f(x) = 8*N and minimum f(x) = 0.
    
    Qualities: maximisation, unconstrained
    '''
    lname = "Goldberg Deceptive 3-bit Function"
    size_equals_parameters = False
    
    max_x = {(0, 0, 0):7, (0, 0, 1):5, (0, 1, 0):5, (0, 1, 1):0,
             (1, 0, 0):3, (1, 0, 1):0, (1, 1, 0):0, (1, 1, 1):8, }
    
    syntax = { 'N?': int } # N = number of 3-bit segments
    default = { 'parameters': 10 }
    
    test_key = (('N', int),)
    test_cfg = ('3', '10', '100')
    
    def __init__(self, cfg=None, **other_cfg):
        super(GoldbergD3B, self).__init__(cfg, **other_cfg)
        
        self.N = self.cfg.N or self.cfg.parameters
        self.size.exact = self.N * 3
        self.size.min = self.size.exact
        self.size.max = self.size.exact
    
    def _eval(self, indiv):
        '''Map each segment of 3-bits and sum for the result.'''
        total = 0
        for i in xrange(0, self.size.exact, 3):
            xi = indiv[i:i+3] # get each block of 3 bits
            total += self.max_x[tuple(xi)]
        return total
    

#=======================================================================
class WhitleyD4B(Binary):
    '''Whitley's Deceptive 4-bit Function
    
    Like Goldberg's Deceptive 3-bit function in form and motivation,
    this deliberately deceptive function has been used to analyse binary
    GAs. This version is extended to 4-bits and is considered harder.
    
    A binary genome must be composed of N * 4 segments, and each segment
    is mapped m() to a value.
        
        f(x) = sum(m(x)),
    
    where the mapping function m() is either a maximisation or
    minimisation set. The maximum f(x) = 30*N and minimum f(x) = 0.
    
    Qualities: maximisation, unconstrained
    '''
    lname = "Whitley Deceptive 4-bit Function"
    size_equals_parameters = False
    
    max_x = {(0, 0, 0, 0):28, (0, 0, 0, 1):26, (0, 0, 1, 0):24, (0, 0, 1, 1):18,
             (0, 1, 0, 0):22, (0, 1, 0, 1):16, (0, 1, 1, 0):14, (0, 1, 1, 1): 0,
             (1, 0, 0, 0):20, (1, 0, 0, 1):12, (1, 0, 1, 0):10, (1, 0, 1, 1): 2,
             (1, 1, 0, 0): 8, (1, 1, 0, 1): 4, (1, 1, 1, 0): 6, (1, 1, 1, 1):30 }
    
    syntax = { 'N?': int } # N = number of 4-bit segments
    default = { 'parameters': 10 }
    
    test_key = (('N', int),)
    test_cfg = ('3', '10', '100')
    
    def __init__(self, cfg=None, **other_cfg):
        super(WhitleyD4B, self).__init__(cfg, **other_cfg)
        
        self.N = self.cfg.N or self.cfg.parameters
        self.size.exact = self.N * 4
        self.size.min = self.size.exact
        self.size.max = self.size.exact
        self.limit = self.size.exact * 30.0
    
    def _eval(self, indiv):
        '''Map each segment of 4-bits and sum for the result.'''
        total = 0
        for i in xrange(0, self.size.exact, 4):
            xi = indiv[i:i+4] # get each block of 4 bits
            total += self.max_x[tuple(xi)]
        return total
    

#=======================================================================
class Multimodal(Binary):
    '''N-dimensional random binary multimodal landscape
    
    See http://www.cs.uwyo.edu/~wspears/multi.html
    
    - Random generator of binary multimodal problems
    - Creates a set of n random L-bit strings, each representing a
      fitness peak
    - Fitness is the number of matching bits to each peak normalised
      (0, 1)
    
    This also seems to be equivalent to P-PEAKS as described by De Jong
    et al (1997). Values of P=100 and N=100 give a medium/high level of
    epistasis (Alba and Troya, 2000).
    
    Qualities: maximisation, multimodal, non-separable, normalised.
    '''
    lname = 'Binary Multimodal (P-PEAKS)'
    size_equals_parameters = False
    
    syntax = { 'N?': int, 'P': int } # N = parameters, P = peaks
    default = { 'parameters': 10, 'P': 4 }
    
    test_key = (('N', int), ('P', int),)
    test_cfg = ('10 4', '100 100') #N=parameters #P=peaks
    
    def __init__(self, cfg=None, **other_cfg):
        super(Multimodal, self).__init__(cfg, **other_cfg)
        
        self.N = N = self.cfg.N or self.cfg.parameters
        self.P = P = self.cfg.P
        
        self.size.min = self.size.max = self.size.exact = N
        # create the random peak[j] templates of length L
        irand = self.rand.randrange
        self._peaks = [[irand(2) for _ in xrange(N)] for _ in xrange(P)]
    
    def _eval(self, indiv):
        '''Fitness is the number of genes in common with the nearest
        peak.
        '''
        tmp = 0.0
        for j in xrange(self.P):
            score = 0.0
            for i in xrange(self.size.exact):
                if indiv[i] == self._peaks[j][i]:
                    score += 1
            if score > tmp:
                tmp = score
        return (tmp / self.size.exact) # 0 = no match, 1.0 = exact match.
    
    def info(self, level):
        '''Return default and add some more peak location info.'''
        result = super(Multimodal, self).info(level)
        result.append('  %d Peaks of %d binary values' % (self.P, self.size.exact))
        result.append('  Peak locations (one per line, limit of 10 shown)')
        for j in xrange(self.P):
            p = self._peaks[j]
            result.append('  ' + ' '.join(str(i) for i in p))
            if j > 10:
                result.append('  ...')
                break
        return result


#=======================================================================
class CNF_SAT(Binary):
    '''N-dimensional random CNF Epistasis Generator
    
    See http://www.cs.uwyo.edu/~wspears/epist.html
    
    - Creates Boolean expression in CNF - SAT Epistasis Generator
    - A "random L-SAT generator" with L literals per clause
    - Code-up of D. Mitchell, B. Selman and H. Levesque (1992)
    
    CNF
        Conjunctive Normal Form
    
    SAT
        SATisfiability of a Boolean expression
    
    " ... This can be used as a generator of epistatic problems - the
    greater the number of clauses the greater the epistasis."
    
    See http://en.wikipedia.org/wiki/Conjunctive_normal_form
    
    - ... "Is there some assignment of T and F that results in T?"
    - A "clause" is an OR'd together list of literals (variables)
    - A "conjunction" is a AND'd set of clauses (the CNF)
    
    Difficult when "the number of clauses is about 4.3 times that number
    of variables" as the "50% satisfiability point".
    
    Also supports the stepwise adaptation of weights (SAW) as suggested
    by Eiben and van der Hauw.
    '''
    lname = 'CNF-SAT'
    size_equals_parameters = False
    
    syntax = {
        'L': int,
        'K': int,
        'N?': int,
        'SAW?': bool
    }
    default = {
        'L': 430, # no of clauses in the expression
        'K': 3, # no of literals per clause
        'N': 100, # no of Boolean variables per literal per clause.
        'SAW': False
    }
    
    test_key = (('L', int), ('K', int), ('N', int), ('SAW', bool),)
    test_cfg = ('430 3 100 SAW', '430 3 100') #L=clauses #K=len #N=var
    
    def __init__(self, cfg=None, **other_cfg):
        super(CNF_SAT, self).__init__(cfg, **other_cfg)
        
        self.n_clauses = self.cfg.L  # L = say < 50000
        self.c_len = self.cfg.K  # K = should be <= 10, say 3
        self.c_vars = self.cfg.N or self.cfg.parameters
        self.use_saw = self.cfg.SAW
        
        self.size.min = self.size.max = self.size.exact = self.c_vars
        
        # create the random clauses of length K (c_len)
        self.c_list = [self._create_clause() for _ in xrange(self.n_clauses)]
        # initialise SAW weights if needed
        if self.use_saw:
            self.w_list = [0] * self.n_clauses
            self.eval = self._eval_saw
        else:
            self.eval = self._eval
    
    def _create_clause(self):
        '''Create a single random clause.
        
        A clause is filled by choosing K variables w/ replacement
        uniformly from the set of all N variables, negating with 50%
        probability.
        '''
        clause = [0] * self.c_len
        irand = self.rand.randrange
        for i in xrange(self.c_len):
            clause[i] = irand(self.c_vars) + 1 # 1 indexed
            if irand(2) == 0:
                clause[i] = -clause[i]
        return clause
    
    def _eval(self, indiv):
        '''Evaluate CNF Boolean Expressions.
        
        Fitness values are between 0.0 and 1.0 if the expression is OK.
        '''
        satisfied = 0
        c_list = self.c_list
        for j in xrange(self.n_clauses):
            for k in xrange(self.c_len):
                if (((c_list[j][k] > 0) and indiv[c_list[j][k] - 1]) or
                    ((c_list[j][k] < 0) and (not indiv[-c_list[j][k] - 1]))):
                    satisfied += 1
                    break
        return (float(satisfied) / self.n_clauses) # 1.0 = satisfied
    
    def _eval_saw(self, indiv):
        '''Evaluate CNF Boolean Expressions using SAW weights
        
        Fitness values are integers between 0 and +INF.
        '''
        total = 0
        c_list = self.c_list
        w_list = self.w_list
        for j in xrange(self.n_clauses):
            for k in xrange(self.c_len):
                if (((c_list[j][k] > 0) and indiv[c_list[j][k] - 1]) or
                    ((c_list[j][k] < 0) and (not indiv[-c_list[j][k] - 1]))):
                    total += w_list[j]
                    break
        return total
    
    def update_saw(self, best):
        '''Update weights using w_i^1 = w - i + 1 + c_i(best).'''
        c_list = self.c_list
        w_list = self.w_list
        for j in xrange(self.n_clauses):
            satisfied = 0 # False
            for k in xrange(self.c_len):
                if (((c_list[j][k] > 0) and best[c_list[j][k] - 1]) or
                    ((c_list[j][k] < 0) and (not best[-c_list[j][k] - 1]))):
                    satisfied = 1 # True
                    break
            # Stepwise Adaptation of Weights - SAW
            # add's 1 while not satisfied, goes to 0 if is satisfied.
            w_list[j] = w_list[j] + 1 - satisfied
    
    
    def info(self, level):
        '''Return the basics, and also and idea of the SAT form.'''
        result = super(CNF_SAT, self).info(level)
        result.append('  Clauses L=%d, Literals/clause K=%d, Variables N=%d' % 
                      (self.n_clauses, self.c_len, self.c_vars))
        result.append('  CNF Clauses (one per line, limit 10 shown)')
        for j in xrange(self.n_clauses):
            result.append('  ' + ''.join('%4d ' % c for c in self.c_list[j]))
            if j > 10:
                result.append('  ...')
                break
        return result

#=======================================================================
class NK(Binary):
    '''NK Landscape Problem Generator
    
    See http://www.cs.uwyo.edu/~wspears/nk.c
    NK Landscape model
    
    Create fitness matrix F = N x (2^{k+1}) of random (0, 1)
    Create epistasis matrix E = N x K with epistasis connections
    
    - ie a hash table per gene of N
    
    Fitness is sum of gene contribution
    
    - gene contribution is its value + contribution of k other values
    
    Qualities: maximisation, normalised
    '''
    lname = 'NK Binary Landscape'
    size_equals_parameters = False
    
    syntax = { 'N?': int, 'K': int }
    default = {
        'parameters': 5, # N = number of genes
        'K': 2, # K = number of interactions (K<=N)
    }
    
    test_key = (('N', int), ('K', int), ('random_seed', int),)
    test_cfg = ('5 2 1234',) #N=genes #K=interactions #seed
    
    def __init__(self, cfg=None, **other_cfg):
        super(NK, self).__init__(cfg, **other_cfg)
        
        n = self.cfg.N or self.cfg.parameters
        k = self.K = self.cfg.K
        self.size.min = self.size.max = self.size.exact = n
        random = self.rand.random
        shuffle = self.rand.shuffle
        
        # Create the BIG fitness matrix N x 2^(K+1) with random(0, 1)
        F = self._F = [None] * n
        f_cols = 2**(k + 1)
        for i in xrange(n):
            F[i] = [random() for _ in xrange(f_cols)]
        
        # Create the epistasis matrix N x K with random index allocations
        E = self._E = [None] * n
        for i in xrange(n):
            links = list(xrange(n)) # all possible links
            links.remove(i) # no epistasis link to self :)
            shuffle(links) # possible links
            E[i] = links[:k] # copy just what we need (the first k links)
    
    
    def _eval(self, indiv):
        '''Evaluate Binary NK landscape.'''
        E = self._E
        F = self._F
        k = self.K
        # calculate the fitness using N-to-K dependencies
        total = 0.0
        for gene in xrange(self.size.exact): # do this for each gene
            fit_index = indiv[gene]
            for i in xrange(k):
                multiplier = 2**(i + 1)
                epi_index = E[gene][i]
                fit_index += multiplier * indiv[epi_index]
            total += F[gene][fit_index]
        # that's it (using total / N as in wspears)
        return total / self.size.exact


#=======================================================================
class NKC(Binary):
    '''NKC Landscape Problem Generator
    
    Note: This problem is for a coevolutionary models and needs multiple
    individuals for evaluation.
    
    - Create fitness matrix F = N x (2^{K+C+1}) of random (0, 1)
    - Create epistasis matrix E = N x (K+C) with epistasis connections
    - Fitness is sum of gene contribution, where gene contribution is
      its value + contribution of k other values
    
    Qualities: maximisation, normalised
    '''
    lname = 'NKC Binary Landscape'
    size_equals_parameters = False
    
    syntax = { 'N?': int, 'K': int, 'C': int, 'group': int }
    default = {
        'parameters': 5, # N = number of genes
        'K': 2, # number of self interactions
        'C': 2, # number of external interactions
        'group': 2, # size of evaluation group
    }
    
    test_key = (('N', int), ('K', int), ('C', int), ('group', int), ('random_seed', int),)
    test_cfg = ('5 2 2 2 1234',) #N #K #C #group #seed
    
    def __init__(self, cfg=None, **other_cfg):
        super(NKC, self).__init__(cfg, **other_cfg)
        
        n = self.cfg.N or self.cfg.parameters
        k = self.K = self.cfg.K
        c = self.C = self.cfg.C
        s = self.group = self.cfg.group
        self.size.min = self.size.max = self.size.exact = n
        random = self.rand.random
        shuffle = self.rand.shuffle
        
        # Create the BIG fitness matrix N x 2^(K+C+1) with random (0, 1)
        F = self._F = [None] * n
        f_cols = 2**(k + c + 1)
        for i in xrange(n):
            F[i] = [random() for _ in xrange(f_cols)]
        
        # Create the epistasis matrix N x (K+C) with random index allocations
        E = self._E = [None] * n
        for i in xrange(n):
            # Add the base K links to self first
            links = [j for j in xrange(n) if j != i] # no epistasis link to self
            shuffle(links)
            E[i] = links[:k]
            # Now add the C links, indexes continue past N
            links = list(xrange(n, n * s))
            shuffle(links)
            E[i].extend(links[:c]) # only what we need
    
    
    def _eval(self, indiv):
        '''Evaluate Binary NKC landscape.
        
        This expects that indiv contains a `JoinedIndividual` with
        ``group`` genomes. The first genome is the one evaluated; the
        others are needed for the C evaluations.
        
        Fitness is assigned to the joined individual and also directly
        to the first individual.
        '''
        assert isinstance(indiv, JoinedIndividual), \
               "indiv (%s) should be JoinedIndividual." % (type(indiv) if indiv else "None")
        assert len(indiv) == self.group
        E = self._E
        F = self._F
        K = self.K
        # Calculate the fitness using N-to-K-to-C dependencies
        total = 0.0
        all_genes = []
        for i in indiv:
            all_genes.extend(i[:])
        
        for i in xrange(len(indiv[0])): # do this for first individual only
            gene = all_genes[i]
            
            multiplier = 1
            for j in xrange(K):
                epi_index = E[gene][j]
                # note - epi_index may be in self -or- another individual!
                gene_index = gene + multiplier * all_genes[epi_index]
                
                multiplier += multiplier
            
            total += F[gene][gene_index]
        # that's it (using total / N as in wspears)
        return total / self.size.exact


#=======================================================================
class MMDP6(Binary):
    '''Massively Multimodal Deceptive Problem (6-bit)
    
    Specifically created to be both deceptive and massively multimodal.
    The deceptive notion is similar to the 3-bit and 4-bit deceptive
    problems, however this problem uses 6-bit binary substring and uses
    the unitation value (number of 1's) mapped to a fitness payoff
    value. The fitness payoff function is bipolar in that there is a
    maximum payoff at both unitation=0, and at unitation=6, with a
    deceptive payoff in the middle.
        
        f(S) = sum(payoff(unitation(s_i)))
    
    where S is the set of 6-bit substrings s_i that make up the solution
    vector x. For any substring of length k there are 2^k global optima,
    however for this version of k=6 there are 22^k local sub-optimum
    values (which certainly fulfills the criteria of "massively"
    deceptive).
    
    The parameter k controls the degree of modality, however in this
    case it is fixed to 6.
    
    See Goldberg et al 1992
    
    Qualities: maximisation, multimodal
    '''
    lname = 'Massively Multimodal Deceptive Problem (6-bit)'
    size_equals_parameters = False
    
    syntax = { 'subs?': int }
    default = { 'parameters': 20 } # substrings, as a reference
    
    test_key = (('subs', int),)
    test_cfg = ('20', '10') #substrings (6-bits each)
    
    # store the payoff values.. could be calculated for general case.
    payoff = [1.0, 0.0, 0.360384, 0.640576, 0.360384, 0.0, 1.0]
    
    def __init__(self, cfg=None, **other_cfg):
        super(MMDP6, self).__init__(cfg, **other_cfg)
        
        self.subs = self.cfg.subs or self.cfg.parameters
        # set total number of binary genes (bits) needed; multiple of 6-bits
        self.size.min = self.size.max = self.size.exact = 6 * self.subs
    
    def _eval(self, indiv):
        '''Evaluate MMDP 6 bit.'''
        total = 0
        payoff = self.payoff
        
        for i in xrange(0, self.size.exact, 6):
            si = indiv[i:i+6] # get each block of 6 bits
            total += payoff[sum(si)] # unitation = sum(si)
        return total


#=======================================================================
class ECC(Binary):
    '''Error Correcting Code Design Problem
    
    See MacWilliams and Sloane (1977) on codes and coding theory.
    See Gamal (1987) using simulated annealing "to design good codes"
    
    - n = length of codeword
    - M = number of codewords
    - d = the minimum Hamming distance between any pair of code words
    
    Goal: find the largest d possible for a given n and M
    Simplify problem by doing M/2 search and create complement for full
    M eg. complement(101) = 010 since its a known quality of good codes.
    
    See http://tracer.lcc.uma.es/problems/ecc/ecc.html
    
    - well known instance n=12, M=12, d=?
    - more complex instance n=12, M=24, d=6
    - harder n=16, M=32, d=8 and n=20, M=40 and d=10 also solved.
    
    See http://mathworld.wolfram.com/Error-CorrectingCode.html
    
    Qualities:
    '''
    lname = 'Error Correcting Code (ECC) Design Problem'
    size_equals_parameters = False
    
    syntax = { 'n': int, 'M': int, 'd': int }
    default = {
        'n': 2, # code length
        'M': 2, # code words
        'd': 1, # min. distance
    }
    
    test_key = (('n', int), ('M', int), ('d', int),)
    test_cfg = ('2 2 1', '12 24 6') #n=code length #M=codewords #d=distance
    
    def __init__(self, cfg=None, **other_cfg):
        super(ECC, self).__init__(cfg, **other_cfg)
        
        self.n = self.cfg.n
        self.M = self.cfg.M
        self.d = self.cfg.d
        # set the number of Binary genes that will be required
        # Note - only using simplified M/2 search space
        self.size.min = self.size.max = self.size.exact = self.n * self.M // 2
    
    def _eval(self, indiv):
        '''Evaluate ECC.'''
        #f(x) = \frac{1}{\sum\limit_{i=1}^M \sum\limit_{j=i, j\neq i}^M d_{ij}^-2  }
        if self.legal(indiv):
            # Sum the distance to other codewords. NOTE: two equal codewords
            # will cause ZeroDivisionError ... so indiv must be legal.
            code = self._splitgenome(indiv)
            total = 0
            dist = self._HammDist
            for i in code:
                #subtotal = 0
                for j in code:
                    if i is not j:
                        total += dist(i, j)**-2
                #total += subtotal
            # Inverse the summed difference
            return 1.0 / total
        else:
            return 0.0001 # penalty factor
    
    def _HammDist(self, v1, v2):
        '''The count of difference components in two vectors (codes).'''
        return sum((1 if i1 != i2 else 0) for i1, i2 in zip(v1, v2))
    
    def _splitgenome(self, indiv):
        '''Split genes into M/2 codewords of length n and creates a
        complement of each for the full M codeword set.
        '''
        n = self.n
        mid = self.M // 2
        code = [None] * self.M
        for i in xrange(mid):
            code[i] = indiv[(i*n):(i*n+n)]
            # create the complementary code also
            code[mid+i] = [(-x + 1) for x in code[i]]
        return code
    
    def legal(self, indiv):
        '''Must check that all codeword pairs have the minimum
        separation distance d. If d is high, it's a highly constricted
        space.
        '''
        dist = self._HammDist
        min_dist = self.d
        code = self._splitgenome(indiv)
        for i in code:
            for j in code:
                if i is j:
                    continue
                if dist(i, j) < min_dist:
                    return False
        # if we reach this, its a legal genome
        return True


#=======================================================================
class SUS(Binary):
    '''Subset Sum Problem Generator
    
    See http://en.wikipedia.org/wiki/Subset_sum_problem
    or Khuri (1994) for a nice description.
    
    This version uses only positive integers:
    
    - N is the number of integers in the full set W
    - S is the subset of W, indicated by a Binary string
    - W is randomly created by drawing from the range [1, 1000)
    - C is created from the sum of a random selection of W elements
    
    If x is a Boolean vector used to indicate the subset then P(x) is
    the sum of W weights selected by the vector x
        
        f(x) = C-P(x) if C-P(x) >= 0 else fitness = P(x)
    
    Qualities: minimisation, NP-complete
    '''
    lname = 'Subset Sum Problem'
    size_equals_parameters = False
    
    syntax = { 'N?': int, 'maxN': int, 'even': bool }
    default = {
        'parameters': 100, # set size (of ints)
        'maxN': 1000, # W_max (random draw size)
        'even': False,
    }
    
    test_key = (('N', int), ('maxN', int), ('random_seed', int), ('even', bool))
    test_cfg = ('100 1000 12345', #
                '100 1000 12345 EVEN',
                '1000 1000 12345') #n=set size #W_max #seed
    
    def __init__(self, cfg=None, **other_cfg):
        super(SUS, self).__init__(cfg, **other_cfg)
        
        self.size.min = self.size.max = self.size.exact = self.cfg.N or self.cfg.parameters
        self.maxN = self.cfg.maxN
        self.even = self.cfg.even
        # Create the set W drawn from range 1..maxn
        frand = self.rand.random
        irand = self.rand.randrange # end-point exclusive [1, 1000)
        if self.even:
            halfMaxN = self.maxN / 2.0
            self._W = [irand(1, halfMaxN + 1)*2 for _ in xrange(self.size.exact)]
            self._S = []
            self._C = self.maxN * (self.size.exact / 4.0) + 1 # an odd number
        else:
            self._W = [irand(1, self.maxN + 1) for _ in xrange(self.size.exact)]
            # Create a random subset S of W and sum, calculate C
            self._S  = [wi for wi in self._W if frand() < 0.5]
            self._C = sum(self._S)
    
    def _eval(self, indiv):
        '''Evaluate subset sum.'''
        # Create an integer subset from the binary selection x (indiv)
        # and sum() to give P(x)
        P_x = sum(wi for wi, xi in zip(self._W, indiv) if xi == 1)
        # get the difference to C
        gap = self._C - P_x
        # return the MINimization value
        if gap >= 0:
            return int(gap) # C-P(x)
        else:
            return int(P_x) # penalty of P(x)
    
    
    def info(self, level):
        '''Return the basics, and also subset sum data.
        '''
        result = super(SUS, self).info(level)
        result.append('  N=%d, maxN=%d, seed=%d' % (self.size.exact, self.maxN, self.cfg.random_seed))
        result.append('  C=%d of %d values' % (self._C, len(self._S)))
        return result

#=======================================================================
class MAXCUT(Binary):
    '''MAXCUT Maximum Cut of a Graph
    
    MAXCUT = maximum cut problem.
    
    - Consider a graph G =(V, E) for a weighted undirected graph.
    - Partition the set of vertices V into two "disjoint" sets V1 and V2
    - Maximise the sum of the weights from edges E that span V1 and V2
    
    NP-Complete problem.
    
    Satisfiability problem (SAT) can be polynomially transformed into
    it. Random cases of N vertices and connection prob P between
    vertices i and j.
    Random weights [0, 1] when allocated.
    
    Qualities:
    '''
    lname = 'MAXCUT'
    size_equals_parameters = False
    
    syntax = { 'N?': int, 'P': [int, float] }
    default = {
        'parameters': 20, # vertices
        'P': 0.9, # probability of connection
    }
    
    test_key = (('N', int), ('P', float),)
    test_cfg = ('20 0.9',) #n=params #p=edge prob.
    
    def __init__(self, cfg=None, **other_cfg):
        super(MAXCUT, self).__init__(cfg, **other_cfg)
        
        self.size.min = self.size.max = self.size.exact = self.cfg.N or self.cfg.parameters
        self.prob = float(self.cfg.P)
        # create adjaceny matrix to represent connections and edge weights
        
        #   0 1 2    i=row, j=col
        # 0 0 - -    "-" means it gets ij value reflected (copied) into it
        # 1 x 0 -    "x" means a weight value is created (prob) b/w [0, 1)
        # 2 x x 0    ...
        frand = self.rand.random
        W = [None]*self.size.exact # init list
        for i in xrange(self.size.exact):
            W[i] = [0]*self.size.exact
            for j in xrange(i): #note: range[0, i) so w[i, j]=0 where i==j
                if frand() < self.prob:
                    W[i][j] = frand() # range [0, 1) ... close enough to [0, 1]?
                    W[j][i] = W[i][j] # reflected connection
        self._W = W # save it for later...
        # Note: don't need the full matrix but leaving as-is for now.
        
        ## Uncomment the following to do the exhaustive test
        ## takes about ~2-5mins for 20.09 graphs.
        ##self._find_best()
    
    def _eval(self, indiv):
        '''Evaluate MAXCUT. Sum the weights of edges that span both
        subgraphs. If indiv[i] = 0 represents V_0 and indiv[i] = 1 is
        V_1.
        '''
        N = self.size.exact
        W = self._W
        total = 0
        for i in xrange(N-1):
            for j in xrange(i + 1, N):
                if indiv[i] != indiv[j]: #only include spanning edges
                    total += W[i][j]
        return total
    
    def info(self, level):
        '''Return the basics, and also MAXCUT data.
        '''
        result = super(MAXCUT, self).info(level)
        result.append('  N=%d, prob=%2.2f, seed N=%d' % (self.size.exact, self.prob, self.cfg.random_seed))
        W = self._W
        for i in W:
            part = ''
            for j in i:
                if j == 0:
                    part += '-.--'
                else:
                    part += '%2.2f' % j
            result.append(part)
        return result
    
    def _find_best(self): #pragma: no cover
        '''Iteratively find the best maxcut for the current random graph
        
        :Note:
            This takes TIME! (~3-5mins). Only call if you *really* want
            to.
        '''
        min_i = 0
        max_i = 2**self.size.exact
        bsf = 0
        bsf_i = 0
        print '*** Doing exhaustive test (%d) to find best. ("." per 10000)' % max_i
        for i in xrange(min_i, max_i):
            x = inttobinlist(i, self.size.exact)
            result = self.eval(x)
            if result > bsf:
                bsf = result
                bsf_i = i
            if i % 10000 == 0:
                print '.', #progress indicator
        print
        print 'Best of %f at %d' % (bsf, bsf_i)


#=======================================================================
class MTTP(Binary):
    '''Minimum Tardy Task Problem (MTTP)
    
    See Stinson 1985/87, Khuri et al. 1994, Giacobini 2005 (phd)
    
    Single processor sequencing to minimise tardy tasks (weights)
    The set of all tasks is T, the selected subset S
    
    - f(x) is minimisation task (minimise sum of tardy task weights)
    
    Each task has (id, length, deadline, penalty weight)
    
    - A selected task must be complete by deadline or penalty applies
    - Tasks are ordered by increasing deadline (gives feasible order)
    - Tasks must be scheduled to start after previous allocated task
      length
    
    Qualities: minimisation
    '''
    lname = 'MTTP'
    size_equals_parameters = False
    
    syntax = { 'tasks?': int }
    default = { 'parameters': 20 }
    
    
    # The following instances from \cite{Khuri1994}
    # pos is id, (task length, deadline, penalty) ordered by increasing deadline
    # optimum 34 (or -34 if inverted)
    mttp5  = [(2, 3, 15),  (4, 5, 20),  (1, 6, 16),  (7, 8, 19),
              (4, 10, 10), (3, 15, 25), (5, 16, 17), (2, 20, 18)]
    
    # optimum 41 (or -41 if inverted)
    mttp20 = [(2, 3, 15),  (4, 5, 20),  (1, 6, 16),   (7, 8, 19),
              (4, 10, 10), (3, 15, 25), (5, 16, 17),  (2, 20, 18),
              (4, 25, 21), (7, 29, 17), (2, 30, 31),  (9, 36, 2),
              (8, 49, 26), (6, 59, 42), (1, 80, 50),  (4, 81, 19),
              (9, 89, 17), (7, 97, 21), (8, 100, 22), (2, 105, 13)]
    
    # This instance is used to generate an instance of n = t*5 (t>1)
    # with an optimum f(x) ==  n*2
    mttp5i = [(3, 5, 60),  (6, 10, 40), (9, 15, 7), (12, 20, 3), (15, 25, 50)]
    
    test_key = (('tasks', int),)
    test_cfg = ('20', '5', '100') # tasks; either 5, 20 or multiple of 5
    
    def __init__(self, cfg=None, **other_cfg):
        super(MTTP, self).__init__(cfg, **other_cfg)
        
        self.size.min = self.size.max = self.size.exact = self.cfg.tasks or self.cfg.parameters
        if self.size.exact == 5:
            self._tasks = self.mttp5
        elif self.size.exact == 20:
            self._tasks = self.mttp20
        elif self.size.exact > 0 and self.size.exact % 5 == 0:
            self._tasks = self._make_mttp5i(self.size.exact // 5)
        else:
            raise ValueError('MTTP tasks must be 5, 20 or multiple of 5 ')
        # Keep the sum total for later reference (eval/penalty etc)
        self._sum = sum(i[2] for i in self._tasks)
    
    def _eval(self, indiv):
        '''Evaluate MTTP subset S defined by x
        
        For feasible solutions a simple weighted sum of tardy tasks
        f(x) = \sum\limits_{i \in T-S} w_i
        '''
        # - Create the T-S set of penalty tasks
        T_S = [t for t, x in zip(self._tasks, indiv) if x == 0] # x[i]==0
        
        # Quick legal version?
        if self.legal(indiv):
            return sum(i[2] for i in T_S)
        
        # Penalty version for infeasible solutions is used instead
        # f(x) = (sum of tardy task wts)
        #        + (sum of tasks wts that made it infeasible)
        #        + (offset penalty of all task wts)
        # - Get the subset of nominated tasks S
        S = [t for t, x in zip(self._tasks, indiv) if x == 1] # x[i]==1
        # - Tasks have (length, deadline, wt)
        time = 0
        for t in S:
            time += t[0] #add the length
            if time > t[1]: # check for deadline bust
                time -= t[0] # reverse the time charge
                T_S.append(t) # move task to the penalty list
        # Now penalty list T_S contains all task that make this invalid
        return (sum(i[2] for i in T_S) + self._sum)
    
    def _eval_legal(self, indiv):
        '''Simple version that assumes all solutions are valid.
        
        f(x) = \sum\limits_{i \in T-S} w_i
        '''
        T_S = [t for t, x in zip(self._tasks, indiv) if not x]
        return sum(i[2] for i in T_S)
    
    def legal(self, indiv):
        '''Checks if all tasks selected can be done within deadlines.
        
        Add up the length of each selected task, check its deadline
        and return True if all okay. (This is not the fitness.)
        '''
        # Get the subset of nominated tasks
        S = [t for t, x in zip(self._tasks, indiv) if x] # x[i]==1
        # Tasks have (length, deadline, wt)
        time = 0
        for t in S:
            time += t[0] #add the length
            if time > t[1]: # check for deadline bust
                return False # leave now!
        # All okay so we're done
        return True
    
    def _make_mttp5i(self, n):
        '''Create a multiple n*mttp5i set of tasks. Optimum will be n*2.
        '''
        # (l, d, w), lj=l(i%5), dj=di+24*m, wj=wi or (m+1)*wi
        result = self.mttp5i*n
        for j, t in enumerate(result):
            j = j + 1 # describe in 1 indexed tasks, so to match...
            # l_j = l_(i % 5) ... which it already is
            l = t[0]
            #d_j = d_i + 24 * m
            m = j // 5
            d = t[1] + 24*m
            # if j % 5 == 3 or j % 5 == 4: w_j = w_i else: (m + 1) * w_i
            if (j % 5 == 3) or (j % 5 == 4):
                w = t[2]
            else:
                w = (m + 1) * t[2]
            # replace
            result[j-1] = (l, d, w)
        # all done
        return result

#=======================================================================
class Graph2c(Binary):
    '''NxN connectivity matrices with odd numbered COLUMN constraints.
    
    The number of dimensions is specified in ``parameters``.
    
    Qualities: maximisation
    '''
    lname = 'Graph2c'
    size_equals_parameters = False
    
    # A value for parameters is required
    syntax = { 'parameters': int }
    
    test_key = (('parameters', int),)
    test_cfg = ('6',)
    test_legal = ([0]*36, [1]*36)
    test_illegal = ([-1]*36, [2]*36)
    
    def __init__(self, cfg=None, **other_cfg):
        super(Graph2c, self).__init__(cfg, **other_cfg)
        
        # Special case: need to handle bounds
        # set the params using the init/bound values
        self.dimensions = self.cfg.parameters
        # Round up to next even number
        if (self.dimensions % 2) == 1: self.dimensions += 1
        self.size.min = self.size.max = self.size.exact = self.dimensions * self.dimensions
        
        self.payoff = [10, -10]*(self.dimensions * self.dimensions // 2)
    
    def _eval(self, indiv):
        '''NxN connectivity matrix. Odd numbered Row constraints
        '''
        if self.legal(indiv):
            fitness = 0
            payoff = self.payoff
            maxpt = self.size.exact - 1
            for i in xrange(self.size.exact):
                if indiv[i] == 1:
                    fitness += payoff[i]
                if i > 0 and (indiv[i-1]==1):
                    fitness += payoff[i-1]
                if i < maxpt and (indiv[i+1]==1):
                    fitness += payoff[i+1]
            return fitness
        else:
            return -(self.dimensions**3) # constraint violation
    
    def info(self, level):
        '''Return payoff matrix table.'''
        result = super(Graph2c, self).info(level) # show the normal info first
        result.append(' Associated payoff matrix is:')
        part = ''
        for i in xrange(self.size.exact):
            part += ('%4d ' % self.payoff[i])
            if not (i + 1) % self.dimensions:
                result.append(part)
                part = ''
        return result

#=======================================================================
class Graph2r(Binary):
    '''NxN connectivity matrices with odd numbered ROW constraints
    
    Qualities:
    '''
    lname = 'Graph2r'
    size_equals_parameters = False
    
    # A value for parameters is required
    syntax = { 'parameters': int }
    
    test_key = (('parameters', int),)
    test_cfg = ('6',)
    test_legal = ([0] * 36, [1] * 36)
    test_illegal = ([-1] * 36, [2] * 36)
    
    def __init__(self, cfg=None, **other_cfg):
        super(Graph2r, self).__init__(cfg, **other_cfg)
        # Special case: need to handle bounds
        # set the params using the init/bound values
        self.dimensions = self.cfg.parameters
        # Round up to next even number
        if (self.dimensions % 2) == 1: self.dimensions += 1
        self.size.min = self.size.max = self.size.exact = self.dimensions * self.dimensions
        
        self.payoff = ([-10] * self.dimensions + [10] * self.dimensions) * (self.dimensions // 2)
    
    def _eval(self, indiv):
        '''NxN connectivity matrix. Odd numbered ROW constraints
        '''
        if self.legal(indiv):
            fitness = 0
            payoff = self.payoff
            maxpt = self.size.exact - 1
            for i in xrange(self.size.exact):
                if indiv[i] == 1:
                    fitness += payoff[i]
                if (i > 0) and (indiv[i-1]==1):
                    fitness += payoff[i-1]
                if (i < maxpt) and (indiv[i+1]==1):
                    fitness += payoff[i+1]
            return fitness
        else:
            return -(self.dimensions**3) # constraint violation
    
    def info(self, level):
        '''Return payoff matrix table.'''
        result = super(Graph2r, self).info(level) # get the normal info first
        result.append(' Associated payoff matrix is:')
        part = ''
        for i in xrange(self.size.exact):
            part += ('%4d ' % self.payoff[i])
            if not (i + 1) % self.dimensions:
                result.append(part)
                part = ''
        return result
