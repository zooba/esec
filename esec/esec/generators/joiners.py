'''A set of join generators that take multiple individuals and
return a set of new individuals based on groups of the original set.

The global variable ``rand`` is made available through the context in
which the joiners are executed.
'''

from itertools import product
from esec.individual import JoinedIndividual
from esec.species import JoinedSpecies
from esec.generators.selectors import BestOnly
from esec.context import rand

def All(srcs, names):
    '''Returns all individuals matched with all other individuals.'''
    for groups in product(*srcs):
        yield JoinedIndividual(groups, names, JoinedSpecies)

def BestWithAll(srcs, names, best_from=0):
    '''Returns the best individual from group `best_from` (zero-based
    index into `srcs`) matched.'''
    srcs = list(srcs)
    best_group = srcs[best_from]
    best = (next(BestOnly(best_group)),)  # make it a tuple
    rest = srcs
    del rest[best_from]
    # reorder names
    if best_from > 0:
        names = names[best_from] + names[:best_from] + names[best_from+1:]
    
    for groups in product(*rest):
        yield JoinedIndividual(best + groups, names, JoinedSpecies)

def Tuples(srcs, names):
    '''Returns all individuals matched with matching elements by index.'''
    for groups in zip(*srcs):
        yield JoinedIndividual(groups, names, JoinedSpecies)

def RandomTuples(srcs, names, distinct=False):
    '''Matches each individual from the first source with randomly
    selected individuals from the other sources.
    
    If `distinct` is ``True``, an attempt is made to avoid repetition
    within a tuple, however, if this cannot be achieved then some
    elements may not be distinct.'''
    choice = rand.choice
    
    srcs = list(srcs)
    assert all(len(i) for i in srcs), 'Empty groups cannot joined'
    for indiv in srcs[0]:
        group = [ indiv ]
        for other_group in srcs[1:]:
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
        yield JoinedIndividual(group, names, JoinedSpecies)

def DistinctRandomTuples(srcs, names):
    '''Matches each individual from the first source with randomly
    selected individuals from the other sources, avoiding repetition
    of individuals within a single tuple.
    '''
    return RandomTuples(srcs, names, distinct=True)
