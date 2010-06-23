from . import *
import random
from esec.generators import joiners

rand = joiners.rand = random

def test_joiners_All():
    population = make_pop()
    
    _gen = joiners.All([population] * 2, ['population'] * 2)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population)**2 = %d" % (len(offspring), len(population)**2)
    assert len(offspring) == len(population)**2, "Did not select all combinations"
    print "Offspring Types: " + ', '.join(set(str(type(s)) for s in offspring))
    assert all(isinstance(g, JoinedIndividual) for g in offspring), "Some individuals are not JoinedIndividuals"
    assert all(all(i in population for i in g.genome) for g in offspring), "Some members are not in original population"
        
def test_joiners_Tuples():
    population = make_pop()
    
    _gen = joiners.Tuples([population] * 3, ['population'] * 3)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "Offspring Types: " + ', '.join(set([str(type(s)) for s in offspring]))
    assert all(isinstance(g, JoinedIndividual) for g in offspring), "Some individuals are not JoinedIndividuals"
    assert all(len(g) == 3 for g in offspring), "Some individuals do not have 3 members"
    assert all(all(i in population for i in g) for g in offspring), "Some members are not in original population"
    assert all(all(i is g[0] for i in g[1:]) for g in offspring), "Some members are not matched with themselves"
    
def test_joiners_RandomTuples():
    population = make_pop()
    
    _gen = joiners.RandomTuples([population] * 3, ['population'] * 3)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "Offspring Types: " + ', '.join(set([str(type(s)) for s in offspring]))
    assert all(isinstance(i, JoinedIndividual) for i in offspring), "Some individuals are not JoinedIndividuals"
    assert all(len(g) == 3 for g in offspring), "Some individuals do not have 3 members"
    assert all(all(i in population for i in g) for g in offspring), "Some members are not in original population"
    assert not all(all(i is g[0] for i in g[1:]) for g in offspring), "All members are matched with themselves"
    
def test_joiners_DistinctRandomTuples():
    population = make_pop()
    
    _gen = joiners.DistinctRandomTuples([population] * 3, ['population'] * 3)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "Offspring Types: " + ', '.join(set([str(type(s)) for s in offspring]))
    assert all(isinstance(i, JoinedIndividual) for i in offspring), "Some individuals are not JoinedIndividuals"
    assert all(len(g) == 3 for g in offspring), "Some individuals do not have 3 members"
    assert all(all(i in population for i in g) for g in offspring), "Some members are not in original population"
    assert all(all(i is not g[0] for i in g[1:]) for g in offspring), "Some members are matched with themselves"
    