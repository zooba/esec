from tests import *
from esec.generators import joiners

def test_joiners():
    print "Maximisation"
    population = make_pop_max()
    yield check_joiners_All, population
    yield check_joiners_Tuples, population
    yield check_joiners_RandomTuples, population
    yield check_joiners_DistinctRandomTuples, population
    
    print "Minimisation"
    population = make_pop_min()
    yield check_joiners_All, population
    yield check_joiners_Tuples, population
    yield check_joiners_RandomTuples, population
    yield check_joiners_DistinctRandomTuples, population
    
    

def check_joiners_All(population):
    _gen = joiners.All([population] * 2, ['population'] * 2)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population)**2 = %d" % (len(offspring), len(population)**2)
    assert len(offspring) == len(population)**2, "Did not select all combinations"
    print "Offspring Types: " + ', '.join(set(str(type(s)) for s in offspring))
    assert all(isinstance(g, JoinedIndividual) for g in offspring), "Some individuals are not JoinedIndividuals"
    assert all(all(i in population for i in g.genome) for g in offspring), "Some members are not in original population"
        
def check_joiners_Tuples(population):
    _gen = joiners.Tuples([population] * 3, ['population'] * 3)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "Offspring Types: " + ', '.join(set([str(type(s)) for s in offspring]))
    assert all(isinstance(g, JoinedIndividual) for g in offspring), "Some individuals are not JoinedIndividuals"
    assert all(len(g) == 3 for g in offspring), "Some individuals do not have 3 members"
    assert all(all(i in population for i in g) for g in offspring), "Some members are not in original population"
    assert all(all(i is g[0] for i in g[1:]) for g in offspring), "Some members are not matched with themselves"
    
def check_joiners_RandomTuples(population):
    _gen = joiners.RandomTuples([population] * 3, ['population'] * 3)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "Offspring Types: " + ', '.join(set([str(type(s)) for s in offspring]))
    assert all(isinstance(i, JoinedIndividual) for i in offspring), "Some individuals are not JoinedIndividuals"
    assert all(len(g) == 3 for g in offspring), "Some individuals do not have 3 members"
    assert all(all(i in population for i in g) for g in offspring), "Some members are not in original population"
    assert not all(all(i is g[0] for i in g[1:]) for g in offspring), "All members are matched with themselves"
    
def check_joiners_DistinctRandomTuples(population):
    _gen = joiners.DistinctRandomTuples([population] * 3, ['population'] * 3)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "Offspring Types: " + ', '.join(set([str(type(s)) for s in offspring]))
    assert all(isinstance(i, JoinedIndividual) for i in offspring), "Some individuals are not JoinedIndividuals"
    assert all(len(g) == 3 for g in offspring), "Some individuals do not have 3 members"
    assert all(all(i in population for i in g) for g in offspring), "Some members are not in original population"
    assert all(all(i is not g[0] for i in g[1:]) for g in offspring), "Some members are matched with themselves"
    