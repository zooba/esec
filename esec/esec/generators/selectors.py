'''A set of selector generators that return some or all of a group of
individuals without modification.

These are distinct from `esec.generators.filters` because they typically
compare individuals against each other (as in ``Best`` or ``Yougest``
selectors). Selectors usually cannot operate on unbounded groups.

The global variable ``rand`` is made available through the context in
which the selectors are executed.
'''

from itertools import cycle, repeat
from math import isinf
from warnings import warn
from esec import esdl_func
from esec.fitness import Fitness
from esec.generators import _key_fitness, _key_birthday
from esec.context import rand

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
    return cycle(group)

@esdl_func('repeat_each')
def RepeatEach(_source, count=2):
    '''Returns each individual `count` times before returning the next.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      count : int
        The number of times to return each individual.
    '''
    assert count is not True, "count has no value"
    count = int(count)
    assert count > 0, "count must be greater than zero"
    for indiv in _source:
        for _ in xrange(count):
            yield indiv

@esdl_func('best')
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
        return iter(sorted(_source, key=_key_fitness, reverse=True))

@esdl_func('best_only')
def BestOnly(_source):
    '''Repeatedly returns the individual with the highest fitness.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    return Best(_source, True)

@esdl_func('worst')
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
        return iter(sorted(_source, key=_key_fitness, reverse=False))

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
        return iter(sorted(_source, key=_key_birthday, reverse=True))

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
        return iter(sorted(_source, key=_key_birthday, reverse=False))

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
               with_replacement=True, without_replacement=False,
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
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.

        Replacement is used if
        ``with_replacement and not without_replacement`` is ``True``.
      
      without_replacement : bool
        ``True`` to remove individuals from contention once they have
        been returned.
      
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
    choice = rand.choice
    # WITH REPLACEMENT
    if with_replacement and not without_replacement:
        group = list(_source)
        size = len(group)
        while True:
            pool = [group[irand(size)] for _ in xrange(k)]
            winner = max(pool, key=_key_fitness)
            if greediness >= 1.0 or frand() < greediness:
                yield winner
            else:
                pool.remove(winner)
                yield choice(pool)
    # WITHOUT REPLACEMENT
    else:
        group = list(_source)
        while group:
            winner_index = 0
            if len(group) >= k:
                pool_index = [irand(len(group)) for _ in xrange(k)]
                winner_index = max(pool_index, key=lambda i: group[i].fitness)
                if not (greediness >= 1.0 or frand() < greediness):
                    pool_index.remove(winner_index)
                    winner_index = choice(pool_index)
            yield group.pop(winner_index)

@esdl_func('binary_tournament')
def BinaryTournament(_source,
                     with_replacement=True, without_replacement=False,
                     greediness=1.0):
    '''Returns a sequence of individuals selected using binary
    tournament selection. Two individuals are selected at random and the
    individual with the best fitness is returned.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
        
        Replacement is used if
        ``with_replacement and not without_replacement`` is ``True``.
      
      without_replacement : bool
        ``True`` to remove individuals from contention once they have
        been returned.
      
      greediness : |prob|
        The probability of the most fit individual being selected. If
        this does not occur, one of the remaining individuals is
        selected at random.
    '''
    return Tournament(_source, k=2,
        with_replacement=with_replacement, without_replacement=without_replacement,
        greediness=greediness)

@esdl_func('uniform_random')
def UniformRandom(_source):
    '''Returns a sequence of individuals selected randomly with replacement,
    without regard to their fitness.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    choice = rand.choice
    group = list(_source)

    while True:
        yield choice(group)

@esdl_func('uniform_shuffle')
def UniformShuffle(_source):
    '''Returns a sequence of individuals selected randomly, without
    regard to their fitness. Each individual is guaranteed to return
    only once, and the number of individuals returned is equal to the
    number in `_source`.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    group = list(_source)
    rand.shuffle(group)
    return iter(group)

@esdl_func('fitness_proportional')
def FitnessProportional(_source,
                        with_replacement=True, without_replacement=False,
                        sus=False, mu=None,
                        offset=None):
    '''Returns a sequence of individuals selected in proportion to their
    fitness. The simplified fitness value
    (`esec.fitness.Fitness.simple`) is used for determining proportion.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
        
        Replacement is used if
        ``with_replacement and not without_replacement`` is ``True``.
        
        If `sus` is ``True``, replacement is not relevant.
      
      without_replacement : bool
        ``True`` to remove individuals from contention once they have
        been returned.
        
      sus : bool
        ``True`` to use stochastic universal sampling (SUS). SUS equally
        spaces selections based on `mu`, resulting in a wider sample
        distribution.
        
        If `sus` is ``True``, replacement is not relevant.
      
      mu : int [optional]
        The number of selections being made when using SUS. If not
        provided, the total number of individuals in `_source` is used.
        
        If `sus` is ``False``, `mu` is ignored.
      
      offset : `Fitness`, `Individual` or iterable(`Individual`)
        The offset to apply to fitness values. If an
        iterable(`Individual`) is passed (for example, a group from
        within an ESDL system), the first individual is used. If
        omitted, the minimum fitness value in `_source` is used.
    '''
    assert offset is not True, "offset has no value"
    assert mu is not True, "mu has no value"
    if sus:
        return FitnessProportionalSUS(_source, mu, offset)
    else:
        return FitnessProportionalNormal(_source,
            with_replacement=(with_replacement and not without_replacement),
            offset=offset)

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


def FitnessProportionalNormal(_source, with_replacement=True, offset=None):
    '''Returns a sequence of individuals selected in proportion to their
    fitness. The simplified fitness value
    (`esec.fitness.Fitness.simple`) is used for determining proportion.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
      
      offset : `Fitness`, `Individual` or iterable(`Individual`)
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
    min_fitness = _GetMinimumFitness(min(i.fitness.simple for i in group), offset)
    
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
        if with_replacement:
            yield wheel[i][1]
        # WITHOUT REPLACEMENT
        else:
            winner = wheel.pop(i)
            total -= winner[0]
            yield winner[1]
            size -= 1

@esdl_func('fitness_sus')
def FitnessProportionalSUS(_source, mu=None, offset=None):
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
      
      offset : `Fitness`, `Individual` or iterable(`Individual`)
        The offset to apply to fitness values. If an
        iterable(`Individual`) is passed (for example, a group from
        within an ESDL system), the first individual is used. If
        omitted, the minimum fitness value in `_source` is used.
    '''
    assert mu is not True, "mu has no value"
    assert offset is not True, "fitness_offset has no value"
    
    group = [indiv for indiv in _source if not isinf(indiv.fitness.simple)]
    group.sort(key=_key_fitness, reverse=True)
    frand = rand.random
    
    if not group: raise StopIteration
    if len(group) == 1:
        yield group[0]
        raise StopIteration
    
    # adjust all fitnesses to be positive
    min_fitness = _GetMinimumFitness(min(i.fitness.simple for i in group), offset)
    
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
                     with_replacement=True, without_replacement=False,
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
      
      with_replacement : bool
        ``False`` to remove individuals from contention once they have
        been returned. The generator terminates when no individuals
        remain and the total number of individuals is equal to the
        number in `_source`. If ``True``, the generator will never
        terminate.
        
        Replacement is used if
        ``with_replacement and not without_replacement`` is ``True``.
        
        If `sus` is ``True``, replacement is not relevant.
      
      without_replacement : bool
        ``True`` to remove individuals from contention once they have
        been returned.
      
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
            with_replacement=(with_replacement and not without_replacement),
            expectation=expectation, neta=neta, invert=invert)

def RankProportionalNormal(_source, with_replacement=True, expectation=1.1, neta=None, invert=False):
    '''Returns a sequence of individuals selected in proportion to their
    rank.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
      
      with_replacement : bool
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
    wheel = [(expectation - 2.0*(expectation-1.0)*i/(size-1.0), j) for i, j in enumerate(group)]
    total = sum(i[0] for i in wheel)
    
    while wheel:
        prob = frand() * total
        
        i = 0
        if size > 1:
            while i < size and prob > wheel[i][0]:
                prob -= wheel[i][0]
                i += 1
            # Fall back on uniform selection if wheel fails
            if i >= size:
                warn('Rank proportional selection wheel failed.')
                i = irand(size)
        
        # WITH REPLACEMENT
        if with_replacement:
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
    wheel = [(expectation - 2.0*(expectation-1.0)*i/(size-1.0), j) for i, j in enumerate(group)]
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

