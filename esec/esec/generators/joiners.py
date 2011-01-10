'''A set of join generators that take multiple individuals and
return a set of new individuals based on groups of the original set.

The global variable ``rand`` is made available through the context in
which the joiners are executed.
'''

from itertools import product, izip
from esec import esdl_func
from esec.species.joined import JoinedIndividual
from esec.generators.selectors import BestOnly
from esec.context import rand

@esdl_func('full_combine')
def All(_source):
    '''Returns all individuals matched with all other individuals.'''
    _source, names = _source
    for groups in product(*_source):
        yield JoinedIndividual(groups, names)

@esdl_func('best_with_rest')
def BestWithAll(_source, best_from=0):
    '''Returns the best individual from group `best_from` (zero-based
    index into `_source`) matched.
    '''
    _source, names = _source
    _source = list(_source)
    best_from = int(best_from)
    best_group = _source[best_from]
    best = (next(BestOnly(best_group)),)  # make it a tuple
    rest = _source
    del rest[best_from]
    # reorder names
    if best_from > 0:
        names = names[best_from] + names[:best_from] + names[best_from+1:]
    
    for groups in product(*rest):
        yield JoinedIndividual(best + groups, names)

@esdl_func('tuples', '_default_join')
def Tuples(_source):
    '''Returns all individuals matched with matching elements by index.
    '''
    _source, names = _source
    for groups in izip(*_source):
        yield JoinedIndividual(groups, names)

@esdl_func('random_tuples')
def RandomTuples(_source, distinct=False):
    '''Matches each individual from the first source with randomly
    selected individuals from the other sources.
    
    If `distinct` is ``True``, an attempt is made to avoid repetition
    within a tuple, however, if this cannot be achieved then some
    elements may not be distinct.
    '''
    choice = rand.choice
    
    _source, names = _source
    _source = list(_source)
    assert all(len(i) for i in _source), 'Empty groups cannot joined'
    for indiv in _source[0]:
        group = [ indiv ]
        for other_group in _source[1:]:
            indiv2 = choice(other_group)
            if distinct:
                # Limit the number of attempts
                limit = len(other_group)
                while indiv2 in group and limit > 0:
                    indiv2 = choice(other_group)
                    limit -= 1
                if limit <= 0:
                    indiv2 = next((i for i in other_group if i not in group), indiv2)
            group.append(indiv2)
        yield JoinedIndividual(group, names)

@esdl_func('distinct_random_tuples')
def DistinctRandomTuples(_source):
    '''Matches each individual from the first source with randomly
    selected individuals from the other sources, avoiding repetition
    of individuals within a single tuple.
    '''
    return RandomTuples(_source, distinct=True)
