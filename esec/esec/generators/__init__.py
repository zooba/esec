'''The default set of joiners, recombiners and selectors for use with
ESDL defined systems.
'''

from esec.fitness import EmptyFitness

def _key_fitness(i):
    '''Used with ``sorted`` to sort by fitness.'''
    return i.fitness  if i else EmptyFitness()
def _key_birthday(i):
    '''Used with ``sorted`` to sort by age.'''
    return i.birthday if i else 0

