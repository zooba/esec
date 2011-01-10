'''The default set of filters, joiners, recombiners and selectors for
use with ESDL defined systems.

In general, all of these elements are referred to as filters. However,
for the sake of separating code into multiple files, they are more
accurately categorised based on their purpose.

All mutation operations belong to individual species.
'''

from esec.fitness import EmptyFitness

def _key_fitness(i):
    '''Used with ``sorted`` to sort by fitness.'''
    return i.fitness  if i else EmptyFitness()
def _key_birthday(i):
    '''Used with ``sorted`` to sort by age.'''
    return i.birthday if i else 0

# Need to load all the modules to ensure `esdl_func` is called for each
# filter.
import esec.generators.filters
import esec.generators.joiners
import esec.generators.selectors
