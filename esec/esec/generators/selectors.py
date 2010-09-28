'''A set of selector generators that return some or all of a group of
individuals without modification.

The global variable ``rand`` is made available through the context in
which the selectors are executed.
'''

from itertools import repeat
from warnings import warn
from esec.generators import _key_fitness
from esec.individual import JoinedIndividual
from esec.context import rand

class NoReplacementSelector(object):
    '''An internal iterator class that supports selection
    of the 'rest' of the population.
    
    It is used to optimise population partitioning by allowing,
    for example, five individuals to be selected at random and
    the remainder to be kept in a separate group.
    '''
    def __init__(self, src, func):
        '''Initialises the iterator.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          src : iterable(`Individual`)
            A sequence of individuals. This sequence is cached in
            a list at construction.
          
          func : function(self, src) |rArr| index
            A function that takes a list of individuals and returns
            the index of the next one selected.
        '''
        self.src = list(src)
        self.func = func
    
    def __iter__(self): return self
    
    def rest(self):
        '''Returns all remaining individuals in the group.
        '''
        return self.src
    
    def next(self):
        '''Returns the next selected individual in the group.
        '''
        if not self.src: raise StopIteration
        
        i = self.func(self, self.src)
        indiv = self.src[i]
        del self.src[i]
        return indiv

def All(src):
    '''Returns all individuals in an unspecified order.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
    '''
    return iter(src)

def Repeat(src):
    '''Returns all individuals in an unspecified order, returning
    to the start when the end is reached.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
    '''
    group = list(src)
    while True:
        for i in group:
            yield i

def Best(src, only=False):
    '''Returns the individuals in decreasing fitness order.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
      
      only : bool
        If ``True``, repeatedly returns only the best individual
        in `src`; otherwise, returns all individuals in `src` in
        order of decreasing fitness.
    '''
    if only:
        return repeat(max(src, key=_key_fitness))
    else:
        return NoReplacementSelector(sorted(src, key=_key_fitness, reverse=True), lambda s, src: 0)

def BestOnly(src):
    '''Repeatedly returns the individual with the highest fitness.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
    '''
    return Best(src, True)

def Worst(src, only=False):
    '''Returns the individuals in increasing fitness order.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
      
      only : bool
        If ``True``, repeatedly returns only the worst individual
        in `src`; otherwise, returns all individuals in `src` in
        order of increasing fitness.
    '''
    if only:
        return repeat(min(src, key=_key_fitness))
    else:
        return NoReplacementSelector(sorted(src, key=_key_fitness, reverse=False), lambda s, src: 0)

def WorstOnly(src):
    '''Repeatedly returns the individual with the lowest fitness.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
    '''
    return Worst(src, True)


def Tournament(src, k=2, replacement=True, greediness=1.0):
    '''Returns a sequence of individuals selected using tournament
    selection. `k` individuals are selected at random and the individual
    with the best fitness is returned.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
      
      k : int |ge| 2
        The number of individuals competing in each tournament.
      
      replacement : bool
        ``False`` to remove individuals from contention once they
        have been returned. The generator terminates when no
        individuals remain and the total number of individuals
        is equal to the number in `src`.
        If ``True``, the generator will never terminate.
      
      greediness : |prob|
        The probability of the most fit individual being
        selected. If this does not occur, one of the remaining
        individuals is selected at random.
    '''
    assert k >= 2, "k must be at least 2"
    irand = rand.randrange
    frand = rand.random
    # WITH REPLACEMENT
    if replacement:
        def _iter(_src):
            '''Performs tournaments on `_src` forever.'''
            size = len(_src)
            while True:
                pool = [_src[irand(size)] for _ in xrange(k)]
                winner = max(pool, key=_key_fitness)
                if greediness >= 1.0 or frand() < greediness:
                    yield winner
                else:
                    pool.remove(winner)
                    yield pool[irand(len(pool))]
        return _iter(list(src))
    # WITHOUT REPLACEMENT
    else:
        def _func(sender, _src):    #pylint: disable=W0613
            '''Performs a tournament on `_src` and returns the winner's index.'''
            if len(_src) >= k:
                pool_index = [irand(len(_src)) for _ in xrange(k)]
                winner_index = max(pool_index, key=lambda i: _src[i].fitness)
                if greediness >= 1.0 or frand() < greediness:
                    return winner_index
                else:
                    pool_index.remove(winner_index)
                    return pool_index[irand(len(pool_index))]
            else:
                # Now everyone's a winner (in fitness order)!
                return 0
        return NoReplacementSelector(src, _func)

def BinaryTournament(src, replacement=True, greediness=1.0):
    '''Returns a sequence of individuals selected using binary tournament
    selection. Two individuals are selected at random and the individual
    with the best fitness is returned.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
      
      replacement : bool
        ``False`` to remove individuals from contention once they
        have been returned. The generator terminates when no
        individuals remain and the total number of individuals
        is equal to the number in `src`.
        If ``True``, the generator will never terminate.
      
      greediness : |prob|
        The probability of the most fit individual being
        selected. If this does not occur, one of the remaining
        individuals is selected at random.
    '''
    return Tournament(src, 2, replacement, greediness)

def UniformRandom(src, replacement=True):
    '''Returns a sequence of individuals selected randomly, without regards
    to their fitness.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
      
      replacement : bool
        ``False`` to remove individuals from contention once they
        have been returned. The generator terminates when no
        individuals remain and the total number of individuals
        is equal to the number in `src`.
        If ``True``, the generator will never terminate.
    '''
    irand = rand.randrange
    # WITH REPLACEMENT
    if replacement:
        def _iter(_src):
            '''Returns random selections forever.'''
            size = len(_src)
            while True:
                yield _src[irand(size)]
        return _iter(list(src))
    # WITHOUT REPLACEMENT
    else:
        return NoReplacementSelector(src, lambda s, _src: irand(len(_src)))

def UniformRandomWithoutReplacement(src):
    '''Returns a sequence of individuals selected randomly, without regards
    to their fitness. Each individual is guaranteed to return only once,
    and the number of individuals returned is equal to the number in `src`.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
    '''
    return UniformRandom(src, replacement=False)

def FitnessProportional(src, replacement=True, sus=False, mu=None):
    '''Returns a sequence of individuals selected in proportion to their
    fitness. Only the most significant fitness value is used for determining
    proportion.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
      
      replacement : bool
        ``False`` to remove individuals from contention once they
        have been returned. The generator terminates when no
        individuals remain and the total number of individuals
        is equal to the number in `src`.
        If ``True``, the generator will never terminate.
        If `sus` is ``True``, `replacement` is ignored.
      
      sus : bool
        ``True`` to use stochastic universal sampling (SUS). SUS
        equally spaces selections based on `mu`, resulting in a
        better sample distribution.
        If `sus` is ``True``, `replacement` is ignored.
      
      mu : int [optional]
        The number of selections being made when using SUS. If
        not provided, the total number of individuals in `src`
        is used.
        If `sus` is ``False``, `mu` is ignored.
    '''
    
    group = sorted(src, key=_key_fitness, reverse=True)
    irand = rand.randrange
    frand = rand.random
    
    if not group: raise StopIteration
    if len(group) == 1:
        yield group[0]
        raise StopIteration
    
    wheel = [(i.fitness.simple, i) for i in group]
    
    # if necessary, adjust all fitnesses to be positive
    min_fitness = min([i[0] for i in wheel])
    if min_fitness < 0:
        wheel = [(i[0]-min_fitness, i[1]) for i in wheel]
    total = sum(i[0] for i in wheel)
    
    size = len(group)
    mu = mu or size
    one_on_mu = 1.0 / mu
    if sus:
        sus_prob = frand() * one_on_mu - one_on_mu
    
    while wheel:
        if sus:
            sus_prob += one_on_mu
            if sus_prob >= 1.0: sus_prob -= 1.0
            prob = sus_prob * total
        else:
            prob = frand() * total
        
        i = 0
        while i < size and prob > wheel[i][0]:
            prob -= wheel[i][0]
            i += 1
        # Fall back on uniform selection if wheel fails
        if i >= size:
            print i, size, sus_prob, prob, total
            warn('Fitness proportional selection wheel failed.')
            i = irand(size)
        
        # WITH REPLACEMENT or SUS
        if replacement or sus:
            yield wheel[i][1]
        # WITHOUT REPLACEMENT
        else:
            winner = wheel.pop(i)
            total -= winner[0]
            yield winner[1]
            size -= 1

def FitnessProportionalSUS(src, mu=None):
    '''Returns a sequence of individuals selected using fitness based
    Stochastic Universal Sampling (SUS).
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
      
      mu : int [optional]
        The number of selections being made. If not provided,
        the total number of individuals in `src` is used.
    '''
    return FitnessProportional(src, sus=True, mu=mu)

def RankProportional(src, replacement=True, sus=False, mu=None):
    '''Returns a sequence of individuals selected in proportion to their
    rank.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
      
      replacement : bool
        ``False`` to remove individuals from contention once they
        have been returned. The generator terminates when no
        individuals remain and the total number of individuals
        is equal to the number in `src`.
        If ``True``, the generator will never terminate.
        If `sus` is ``True``, `replacement` is ignored.
      
      sus : bool
        ``True`` to use stochastic universal sampling (SUS). SUS
        equally spaces selections based on `mu`, resulting in a
        better sample distribution.
        If `sus` is ``True``, `replacement` is ignored.
      
      mu : int [optional]
        The number of selections being made when using SUS. If
        not provided, the total number of individuals in `src`
        is used.
        If `sus` is ``False``, `mu` is ignored.
    '''
    
    group = sorted(src, key=_key_fitness, reverse=True)
    frand = rand.random     #pylint: disable=E0602
    irand = rand.randrange  #pylint: disable=E0602
    
    size = len(group)
    mu = mu or size
    one_on_mu = 1.0 / mu
    wheel = [(size - i, j) for i, j in enumerate(group)]
    total = sum([i[0] for i in wheel])
    
    if sus:
        sus_prob = frand() * one_on_mu - one_on_mu
    
    while wheel:
        if sus:
            sus_prob += one_on_mu
            if sus_prob > 1.0: sus_prob -= 1.0
            prob = int(sus_prob * total)
        else:
            prob = irand(total)
        
        i = 0
        while i < size and prob > wheel[i][0]:
            prob -= wheel[i][0]
            i += 1
        # Fall back on uniform selection if wheel fails
        if i >= size:
            warn('Rank proportional selection wheel failed.')
            i = irand(size)
        
        # WITH REPLACEMENT or SUS
        if replacement or sus:
            yield wheel[i][1]
        # WITHOUT REPLACEMENT
        else:
            winner = wheel.pop(i)
            total -= winner[0]
            yield winner[1]
            size -= 1

def RankProportionalSUS(src, mu=None):
    '''Returns a sequence of individuals selected using rank based
    Stochastic Universal Sampling (SUS).
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
      
      mu : int [optional]
        The number of selections being made. If not provided,
        the total number of individuals in `src` is used.
    '''
    return RankProportional(src, sus=True, mu=mu)

def Unique(src):
    '''Returns a sequence of the unique individuals based on phenomes.
    
    Individuals are compared using their ``phenome_string`` property.
    
    :Parameters:
      src : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are
        returned from this sequence, depending on the selection
        criteria.
    '''
    known = set()
    
    for indiv in src:
        phenome = indiv.phenome_string
        if phenome not in known:
            known.add(phenome)
            yield indiv

def BestOfTuple(src):
    '''Returns a sequence of the individuals with highest fitness from
    each `JoinedIndividual` provided.

    :Parameters:
      src : iterable(`JoinedIndividual`)
        A sequence of joined individuals.
    '''

    for indiv in src:
        assert isinstance(indiv, JoinedIndividual), "JoinedIndividuals are required for BestOfTuple"
        yield max(indiv, key=_key_fitness)
