from tests import *
from itertools import izip
from esec.context import rand, notify
from esec.generators import filters

def test_selectors_max():
    population = make_pop_max()
    yield check_filters_Unique, population, make_best_pop_max()
    yield check_filters_Legal, population
    yield check_filters_Illegal, population
    
def test_selectors_min():
    population = make_pop_min()
    yield check_filters_Unique, population, make_best_pop_min()
    yield check_filters_Legal, population
    yield check_filters_Illegal, population

def check_filters_Unique(population1, population2):
    _gen = filters.Unique(_source=iter(population1))
    offspring = list(_gen)
    
    print 'Offspring:\n' + '\n'.join(indiv.phenome_string for indiv in offspring)
    assert len(offspring) == len(population1), "Did not select all individuals"
    
    _gen = filters.Unique(_source=iter(population2))
    offspring = list(_gen)
    
    print 'Offspring:\n' + '\n'.join(indiv.phenome_string for indiv in offspring)
    assert len(offspring) == 1, "Did not select single individual"
    

def check_filters_Legal(population):
    _gen = filters.Legal(_source=iter(population))
    offspring = list(_gen)
    
    print 'Offspring:\n' + '\n'.join(indiv.phenome_string for indiv in offspring)
    assert len(offspring) == len(population), "Did not select all individuals"

def check_filters_Illegal(population):
    _gen = filters.Illegal(_source=iter(population))
    offspring = list(_gen)
    
    print 'Offspring:\n' + '\n'.join(indiv.phenome_string for indiv in offspring)
    assert len(offspring) == 0, "Did not select zero individuals"
