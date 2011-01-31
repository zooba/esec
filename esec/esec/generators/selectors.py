'''A set of selector generators that return some or all of a group of
individuals without modification.

These are distinct from `esec.generators.filters` because they typically
compare individuals against each other (as in ``Best`` or ``Yougest``
selectors). Selectors usually cannot operate on unbounded groups.

The global variable ``rand`` is made available through the context in
which the selectors are executed.
'''

from itertools import repeat
from math import isinf
from warnings import warn
from esec import esdl_func
from esec.fitness import Fitness
from esec.generators import _key_fitness, _key_birthday
from esec.species.joined import JoinedIndividual
from esec.context import rand

class NoReplacementSelector(object):
    '''An internal iterator class that supports selection of the 'rest'
    of the population.
    
    It is used to optimise population partitioning by allowing, for
    example, five individuals to be selected at random and the remainder
    to be kept in a separate group.
    '''
    def __init__(self, _source, func):
        '''Initialises the iterator.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. This sequence is cached in a list
            at construction.
          
          func : function(self, _source) |rArr| index
            A function that takes a list of individuals and returns the
            index of the next one selected.
        '''
        self._source = list(_source)
        self.func = func
    
    def __iter__(self): return self
    
    def rest(self):
        '''Returns all remaining individuals in the group.'''
        return self._source
    
    def next(self):
        '''Returns the next selected individual in the group.'''
        if not self._source: raise StopIteration
        
        i = self.func(self, self._source)
        indiv = self._source[i]
        del self._source[i]
        return indiv

@esdl_func('select_all')
def All(_source):
    '''Returns all individuals in an unspecified order.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    return iter(_source)

@esdl_func('repeated')
def Repeat(_source):
    '''Returns all individuals in an unspecified order, returning to the
    start when the end is reached.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    group = list(_source)
    while True:
        for i in group:
            yield i

@esdl_func('best', 'truncate_best')
def Best(_source, only=False):
    '''Returns the individuals in decreasing fitness order.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      only : bool
        If ``True``, repeatedly returns only the best individual in
        `_source`; otherwise, returns all individuals in `_source` in
        order of decreasing fitness.
    '''
    if only:
        return repeat(max(_source, key=_key_fitness))
    else:
        return NoReplacementSelector(sorted(_source, key=_key_fitness, reverse=True), lambda s, _source: 0)

@esdl_func('best_only')
def BestOnly(_source):
    '''Repeatedly returns the individual with the highest fitness.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    return Best(_source, True)

@esdl_func('worst', 'truncate_worst')
def Worst(_source, only=False):
    '''Returns the individuals in increasing fitness order.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      only : bool
        If ``True``, repeatedly returns only the worst individual in
        `_source`; otherwise, returns all individuals in `_source` in
        order of increasing fitness.
    '''
    if only:
        return repeat(min(_source, key=_key_fitness))
    else:
        return NoReplacementSelector(sorted(_source, key=_key_fitness, reverse=False), lambda s, _source: 0)

@esdl_func('worst_only')
def WorstOnly(_source):
    '''Repeatedly returns the individual with the lowest fitness.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    return Worst(_source, True)

@esdl_func('youngest')
def Youngest(_source, only=False):
    '''Returns the individuals in decreasing birthdate order.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      only : bool
        If ``True``, repeatedly returns only the youngest individual in
        `_source`; otherwise, returns all individuals in `_source` in
        order of decreasing birthdates.
    '''
    if only:
        return repeat(max(_source, key=_key_birthday))
    else:
        return NoReplacementSelector(sorted(_source, key=_key_birthday, reverse=True), lambda s, _source: 0)

@esdl_func('youngest_only')
def YoungestOnly(_source):
    '''Repeatedly returns the individual with the latest birthday.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    return Youngest(_source, True)

@esdl_func('oldest')
def Oldest(_source, only=False):
    '''Returns the individuals in increasing birthdate order.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      only : bool
        If ``True``, repeatedly returns only the oldest individual in
        `_source`; otherwise, returns all individuals in `_source` in
        order of increasing birthdates.
    '''
    if only:
        return repeat(min(_source, key=_key_birthday))
    else:
        return NoReplacementSelector(sorted(_source, key=_key_birthday, reverse=False), lambda s, _source: 0)

@esdl_func('oldest_only')
def OldestOnly(_source):
    '''Repeatedly returns the individual with the earliest birthday.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    return Oldest(_source, True)

@esdl_func('tournament')
def Tournament(_source, k=2,
               replacement=True,   # for back-compat
               with_replacement=False, without_replacement=False,   #pylint: disable=W0613
               greediness=1.0):
    '''Returns a sequence of individuals selected using tournament
    selection. `k` individuals are selected at random and the individual
    with the best fitness is returned.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      k : int |ge| 2
        The number of individuals competing in each tournament.
      
      replacement : bool
        For backwards compatibility. Use either `with_replacement` or
        `without_replacement`.
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
      
      without_replacement : bool
        ``True`` to remove individuals from contention once they have
        been returned.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
      
      greediness : |prob|
        The probability of the most fit individual being selected. If
        this does not occur, one of the remaining individuals is
        selected at random.
    '''
    assert k is not True, "k has no value"
    assert greediness is not True, "greediness has no value"
    k = int(k)
    assert k >= 2, "k must be at least 2"
    irand = rand.randrange
    frand = rand.random
    # WITH REPLACEMENT (replacement test is for back-compat)
    if replacement and not without_replacement:
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
        return _iter(list(_source))
    # WITHOUT REPLACEMENT
    else:
        def _func(sender, _src):    #pylint: disable=W0613
            '''Performs a tournament on `_src` and returns the winner's
            index.
            '''
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
        return NoReplacementSelector(_source, _func)

@esdl_func('binary_tournament')
def BinaryTournament(_source,
                     replacement=True,
                     with_replacement=False, without_replacement=False,
                     greediness=1.0):
    '''Returns a sequence of individuals selected using binary
    tournament selection. Two individuals are selected at random and the
    individual with the best fitness is returned.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      replacement : bool
        For backwards compatibility. Use either `with_replacement` or
        `without_replacement`.
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
      
      without_replacement : bool
        ``True`` to remove individuals from contention once they have
        been returned.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
      
      greediness : |prob|
        The probability of the most fit individual being selected. If
        this does not occur, one of the remaining individuals is
        selected at random.
    '''
    return Tournament(_source, k=2,
        replacement=replacement,
        with_replacement=with_replacement, without_replacement=without_replacement,
        greediness=greediness)

@esdl_func('uniform_random')
def UniformRandom(_source,
                  replacement=True,     # for back-compat
                  with_replacement=False, without_replacement=False):   #pylint: disable=W0613
    '''Returns a sequence of individuals selected randomly, without
    regard to their fitness.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      replacement : bool
        For backwards compatibility. Use either `with_replacement` or
        `without_replacement`.
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
      
      without_replacement : bool
        ``True`` to remove individuals from contention once they have
        been returned.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
    '''
    irand = rand.randrange
    # WITH REPLACEMENT
    if replacement and not without_replacement:
        def _iter(_src):
            '''Returns random selections forever.'''
            size = len(_src)
            while True:
                yield _src[irand(size)]
        return _iter(list(_source))
    # WITHOUT REPLACEMENT
    else:
        return NoReplacementSelector(_source, lambda s, _src: irand(len(_src)))

@esdl_func('uniform_random_no_replacement', 'uniform_shuffle')
def UniformRandomWithoutReplacement(_source):
    '''Returns a sequence of individuals selected randomly, without
    regard to their fitness. Each individual is guaranteed to return
    only once, and the number of individuals returned is equal to the
    number in `_source`.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    return UniformRandom(_source, without_replacement=True)

@esdl_func('fitness_proportional')
def FitnessProportional(_source,
                        replacement=True,   # for back-compat
                        with_replacement=False, without_replacement=False,  #pylint: disable=W0613
                        sus=False, mu=None,
                        fitness_offset=None):
    '''Returns a sequence of individuals selected in proportion to their
    fitness. The simplified fitness value
    (`esec.fitness.Fitness.simple`) is used for determining proportion.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      replacement : bool
        For backwards compatibility. Use either `with_replacement` or
        `without_replacement`.
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
        
        If `sus` is ``True``, replacement is not relevant.
      
      without_replacement : bool
        ``True`` to remove individuals from contention once they have
        been returned.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
        
        If `sus` is ``True``, replacement is not relevant.
      
      sus : bool
        ``True`` to use stochastic universal sampling (SUS). SUS equally
        spaces selections based on `mu`, resulting in a wider sample
        distribution.
        
        If `sus` is ``True``, replacement is not relevant.
      
      mu : int [optional]
        The number of selections being made when using SUS. If not
        provided, the total number of individuals in `_source` is used.
        
        If `sus` is ``False``, `mu` is ignored.
      
      fitness_offset : `Fitness`, `Individual` or iterable(`Individual`)
        The offset to apply to fitness values. If an
        iterable(`Individual`) is passed (for example, a group from
        within an ESDL system), the first individual is used. If
        omitted, the minimum fitness value in `_source` is used.
    '''
    assert fitness_offset is not True, "fitness_offset has no value"
    assert mu is not True, "mu has no value"
    if sus:
        return FitnessProportionalSUS(_source, mu, fitness_offset)
    else:
        return FitnessProportionalNormal(_source,
            replacement=(replacement and not without_replacement),
            fitness_offset=fitness_offset)

def _GetMinimumFitness(fitness1, fitness2):
    '''Returns the minimum of two fitness values.
    
    `fitness1` or `fitness2` may be an instance of `Fitness`, an object
    providing a ``fitness`` attribute or a sequence containing either of
    these two objects.
    '''
    if fitness1 is None: return fitness2
    
    if isinstance(fitness1, Fitness): fitness1 = fitness1.simple
    elif hasattr(fitness1, 'fitness'): fitness1 = fitness1.fitness.simple
    elif hasattr(fitness1, '__iter__'): fitness1 = _GetMinimumFitness(next(iter(fitness1)), None)
    
    if fitness2 is None: return fitness1
    
    fitness2 = _GetMinimumFitness(fitness2, None)
    
    return fitness1 if fitness2 > fitness1 else fitness2


def FitnessProportionalNormal(_source, replacement=True, fitness_offset=None):
    '''Returns a sequence of individuals selected in proportion to their
    fitness. The simplified fitness value
    (`esec.fitness.Fitness.simple`) is used for determining proportion.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
      
      fitness_offset : `Fitness`, `Individual` or iterable(`Individual`)
        The offset to apply to fitness values. If an
        iterable(`Individual`) is passed (for example, a group from
        within an ESDL system), the first individual is used. If
        omitted, the minimum fitness value in `_source` is used.
    '''
    group = [indiv for indiv in _source if not isinf(indiv.fitness.simple)]
    group.sort(key=_key_fitness, reverse=True)
    irand = rand.randrange
    frand = rand.random
    
    if not group: raise StopIteration
    if len(group) == 1:
        yield group[0]
        raise StopIteration
    
    # adjust all fitnesses to be positive
    min_fitness = _GetMinimumFitness(min(i.fitness.simple for i in group), fitness_offset)
    
    size = len(group)
    wheel = [(i.fitness.simple - min_fitness, i) for i in group]
    assert all(i[0] >= 0.0 for i in wheel), "Fitness scaling failed"
    total = sum(i[0] for i in wheel)
    
    while wheel:
        prob = frand() * total
        
        i = 0
        while i < size and prob > wheel[i][0]:
            prob -= wheel[i][0]
            i += 1
        # Fall back on uniform selection if wheel fails
        if i >= size:
            warn('Fitness proportional selection wheel failed.')
            i = irand(size)
        
        # WITH REPLACEMENT
        if replacement:
            yield wheel[i][1]
        # WITHOUT REPLACEMENT
        else:
            winner = wheel.pop(i)
            total -= winner[0]
            yield winner[1]
            size -= 1

@esdl_func('fitness_sus')
def FitnessProportionalSUS(_source, mu=None, fitness_offset=None):
    '''Returns a sequence of individuals selected using fitness based
    Stochastic Universal Sampling (SUS). The simplified fitness value
    (`esec.fitness.Fitness.simple`) is used for determining proportion.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      mu : int [optional]
        The number of selections being made. If not provided, the total
        number of individuals in `_source` is used.
      
      fitness_offset : `Fitness`, `Individual` or iterable(`Individual`)
        The offset to apply to fitness values. If an
        iterable(`Individual`) is passed (for example, a group from
        within an ESDL system), the first individual is used. If
        omitted, the minimum fitness value in `_source` is used.
    '''
    assert mu is not True, "mu has no value"
    assert fitness_offset is not True, "fitness_offset has no value"
    
    group = [indiv for indiv in _source if not isinf(indiv.fitness.simple)]
    group.sort(key=_key_fitness, reverse=True)
    frand = rand.random
    
    if not group: raise StopIteration
    if len(group) == 1:
        yield group[0]
        raise StopIteration
    
    # adjust all fitnesses to be positive
    min_fitness = _GetMinimumFitness(min(i.fitness.simple for i in group), fitness_offset)
    
    size = len(group)
    wheel = [(i.fitness.simple - min_fitness, i) for i in group]
    assert all(i[0] >= 0.0 for i in wheel), "Fitness scaling failed"
    total = sum(i[0] for i in wheel)
    
    mu = int(mu or size)
    prob_delta = total / mu
    prob = frand() * prob_delta - prob_delta
    i = 0
    change_level = wheel[0][0]
    while True:
        prob += prob_delta
        while prob > change_level:
            i += 1
            while i >= size: i -= size
            change_level += wheel[i][0]
        yield wheel[i][1]

@esdl_func('rank_proportional')
def RankProportional(_source,
                     replacement=True,  # for back-compat
                     with_replacement=False, without_replacement=False, #pylint: disable=W0613
                     expectation=1.1, neta=None,
                     invert=False,
                     sus=False, mu=None):
    '''Returns a sequence of individuals selected in proportion to their
    rank.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      replacement : bool
        For backwards compatibility. Use either `with_replacement` or
        `without_replacement`.
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
        
        If `sus` is ``True``, replacement is ignored.
      
      without_replacement : bool
        ``True`` to remove individuals from contention once they have
        been returned.
        
        If both `with_replacement` and `without_replacement` are
        ``False``, `with_replacement` is the default.
        
        If `sus` is ``True``, replacement is ignored.
      
      expectation : float |isin| [1.0, 2.0]
        The relative probability of selecting the highest ranked
        individual. Defaults to 1.1.
        
        If `neta` is provided, its value is used instead.
      
      neta : float
        A synonym for `expectation`.
      
      invert : bool [optional]
        ``False`` to give the highest probabilities to the most fit
        individuals; otherwise, ``True`` to give the highest
        probabilities to the least fit individuals.
      
      sus : bool
        ``True`` to use stochastic universal sampling (SUS). SUS equally
        spaces selections based on `mu`, resulting in a wider sample
        distribution.
        
        If `sus` is ``True``, replacement is ignored.
      
      mu : int [optional]
        The number of selections being made when using SUS. If not
        provided, the total number of individuals in `_source` is used.
        
        If `sus` is ``False``, `mu` is ignored.
    '''
    assert expectation is not True, "expectation has no value"
    assert neta is not True, "neta has no value"
    assert mu is not True, "mu has no value"
    if sus:
        return RankProportionalSUS(_source, mu, expectation, neta, invert)
    else:
        return RankProportionalNormal(_source,
            replacement=(replacement and not without_replacement),
            expectation=expectation, neta=neta, invert=invert)

def RankProportionalNormal(_source, replacement=True, expectation=1.1, neta=None, invert=False):
    '''Returns a sequence of individuals selected in proportion to their
    rank.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
      
      expectation : float |isin| [1.0, 2.0]
        The relative probability of selecting the highest ranked
        individual. Defaults to 1.1.
        
        If `neta` is provided, its value is used instead.
      
      neta : float
        A synonym for `expectation`.
      
      invert : bool [optional]
        ``False`` to give the highest probabilities to the most fit
        individuals; otherwise, ``True`` to give the highest
        probabilities to the least fit individuals.
    '''
    group = [indiv for indiv in _source if not isinf(indiv.fitness.simple)]
    group.sort(key=_key_fitness, reverse=not invert)
    irand = rand.randrange
    frand = rand.random
    
    if not group: raise StopIteration
    if len(group) == 1:
        yield group[0]
        raise StopIteration
    
    if neta is not None: expectation = neta
    size = len(group)
    wheel = [(expectation - 2.0*(expectation-1.0)*(i-1.0)/(size-1.0), j) for i, j in enumerate(group)]
    total = sum(i[0] for i in wheel)
    
    while wheel:
        prob = frand() * total
        
        i = 0
        while i < size and prob > wheel[i][0]:
            prob -= wheel[i][0]
            i += 1
        # Fall back on uniform selection if wheel fails
        if i >= size:
            warn('Rank proportional selection wheel failed.')
            i = irand(size)
        
        # WITH REPLACEMENT
        if replacement:
            yield wheel[i][1]
        # WITHOUT REPLACEMENT
        else:
            winner = wheel.pop(i)
            total -= winner[0]
            yield winner[1]
            size -= 1

@esdl_func('rank_sus')
def RankProportionalSUS(_source, mu=None, expectation=1.1, neta=None, invert=False):
    '''Returns a sequence of individuals using rank-based Stochastic
    Uniform Sampling (SUS).
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      expectation : float |isin| [1.0, 2.0]
        The relative probability of selecting the highest ranked
        individual. Defaults to 1.1.
        
        If `neta` is provided, its value is used instead.
      
      neta : float
        A synonym for `expectation`.
      
      invert : bool [optional]
        ``False`` to give the highest probabilities to the most fit
        individuals; otherwise, ``True`` to give the highest
        probabilities to the least fit individuals.
      
      mu : int [optional]
        The number of selections being made when using SUS. If not
        provided, the total number of individuals in `_source` is used.
    '''
    assert mu is not True, "mu has no value"
    assert expectation is not True, "expectation has no value"
    assert neta is not True, "neta has no value"
    group = [indiv for indiv in _source if not isinf(indiv.fitness.simple)]
    group.sort(key=_key_fitness, reverse=not invert)
    frand = rand.random
    
    if not group: raise StopIteration
    if len(group) == 1:
        yield group[0]
        raise StopIteration
    
    if neta is not None: expectation = neta
    size = len(group)
    wheel = [(expectation - 2.0*(expectation-1.0)*(i-1.0)/(size-1.0), j) for i, j in enumerate(group)]
    total = sum(i[0] for i in wheel)
    
    mu = int(mu or size)
    prob_delta = total / mu
    prob = frand() * prob_delta - prob_delta
    i = 0
    change_level = wheel[0][0]
    while True:
        prob += prob_delta
        while prob > change_level:
            i += 1
            while i >= size: i -= size
            change_level += wheel[i][0]
        yield wheel[i][1]

@esdl_func('best_of_tuple')
def BestOfTuple(_source):
    '''Returns a sequence of the individuals with highest fitness from
    each `JoinedIndividual` provided.

    :Parameters:
      _source : iterable(`JoinedIndividual`)
        A sequence of joined individuals.
    '''

    for indiv in _source:
        assert isinstance(indiv, JoinedIndividual), "JoinedIndividuals are required for BestOfTuple"
        yield max(indiv, key=_key_fitness)
