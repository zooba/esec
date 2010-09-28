from . import *
import random
from esec.generators import recombiners, joiners

rand = recombiners.rand = random

make_pop = make_pop_max
make_pop_variable = make_pop_variable_max

def test_recombiners_OnePointSame_Values():
    population = make_pop()
    
    _gen = recombiners.OnePointSame(iter(population))
    child1, child2 = next(_gen), next(_gen)
    print "len(child1) = %d, len(child2) = %d, len(population[0]) = %d" % (len(child1), len(child2), len(population[0]))
    assert len(child1) == len(child2) == len(population[0]), "Individual's length was changed"
    child1_set, child2_set = set(child1.genome), set(child2.genome)
    print "len(set(child1)) = %d, len(set(child2)) = %d" % (len(child1_set), len(child2_set))
    assert len(child1_set) == len(child2_set) == 2, "Number of distinct values is not 2"
    print "set(child1) = %s" % child1_set
    print "set(child2) = %s" % child2_set
    assert child1_set == child2_set, "Distinct values are not matched"

def test_recombiners_OnePointSame_Selection_All():
    population = make_pop()
    
    _gen = recombiners.OnePointSame(iter(population))
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "intersection = %s" % set(offspring).intersection(set(population))
    assert len(set(offspring).intersection(set(population))) == 0, "Did not modify some individuals"

def test_recombiners_OnePointSame_Selection_None():
    population = make_pop()
    
    _gen = recombiners.OnePointSame(iter(population), per_pair_rate=0.0)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "difference = %s" % set(offspring).difference(set(population))
    assert len(set(offspring).difference(set(population))) == 0, "Did not modify any individuals"

def test_recombiners_OnePointSame_Selection_Half():
    population = make_pop_variable()
    
    modify_count = 0
    for _ in xrange(100):
        _gen = recombiners.OnePointSame(iter(population), per_pair_rate=0.5)
        offspring = list(_gen)
        assert len(offspring) == len(population), "Did not select all individuals"
        modify_count += len(set(offspring).difference(set(population)))
    modify_rate = float(modify_count) / (100.0 * len(population))
    assert 0.4 <= modify_rate <= 0.6, "Did not modify approximately 50% of individuals"

def test_recombiners_OnePointDifferent_Values():
    population = make_pop_variable()
    
    _gen = recombiners.OnePointDifferent(iter(population))
    child1, child2 = next(_gen), next(_gen)
    print "len(child1) = %d, len(child2) = %d, len(pop[0]) = %d, len(pop[1]) = %d" % (len(child1), len(child2), len(population[0]), len(population[1]))
    assert len(child1) + len(child2) == len(population[0]) + len(population[1]), "Genes were gained/lost"
    child1_set, child2_set = set(child1.genome), set(child2.genome)
    source_set = set(population[0].genome).union(set(population[1].genome))
    print "len(set(child1)) = %d, len(set(child2)) = %d" % (len(child1_set), len(child2_set))
    assert len(child1_set) <= 2 and len(child2_set) <= 2, "Number of distinct values is not 2 or less"
    print "set(child1) = %s" % child1_set
    print "set(child2) = %s" % child2_set
    print "set(pop[0] U pop[1]) = %s" % source_set
    assert child1_set.issubset(source_set) and child2_set.issubset(source_set), "Genes were invented"

def test_recombiners_OnePointDifferent_Selection_All():
    population = make_pop_variable()
    
    _gen = recombiners.OnePointDifferent(iter(population))
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "intersection = %s" % set(offspring).intersection(set(population))
    assert len(set(offspring).intersection(set(population))) == 0, "Did not modify some individuals"

def test_recombiners_OnePointDifferent_Selection_None():
    population = make_pop_variable()
    
    _gen = recombiners.OnePointDifferent(iter(population), per_pair_rate=0.0)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "difference = %s" % set(offspring).difference(set(population))
    assert len(set(offspring).difference(set(population))) == 0, "Did not modify any individuals"

def test_recombiners_OnePointDifferent_Selection_Half():
    population = make_pop_variable()
    
    modify_count = 0
    for _ in xrange(100):
        _gen = recombiners.OnePointDifferent(iter(population), per_pair_rate=0.5)
        offspring = list(_gen)
        assert len(offspring) == len(population), "Did not select all individuals"
        modify_count += len(set(offspring).difference(set(population)))
    modify_rate = float(modify_count) / (100.0 * len(population))
    assert 0.4 <= modify_rate <= 0.6, "Did not modify approximately 50% of individuals"

def test_recombiners_PerGeneTuple_None():
    population = make_pop()
    joined = list(joiners.DistinctRandomTuples([population] * 2, ['population'] * 2))
    
    _gen = recombiners.PerGeneTuple(joined, per_indiv_rate=1.0, per_gene_rate=1.0)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    assert all(g1 is g2 for g1, g2 in zip(population, offspring)), "Did not return first individual"

def test_recombiners_PerGeneTuple_NotFromFirst():
    population = make_pop()
    joined = list(joiners.DistinctRandomTuples([population] * 2, ['population'] * 2))
    
    _gen = recombiners.PerGeneTuple(joined, per_indiv_rate=1.0, per_gene_rate=0.0)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    assert all(g1 is not g2 for g1, g2 in zip(population, offspring)), "DistinctRandom failed"
    assert all(g not in population for g in offspring), "Some individuals were not cloned"
    assert sum(g.statistic.get('recombined', 0) for g in offspring) == len(offspring), "Some individuals were not recombined"

def test_recombiners_PerGeneTuple_AutoProb():
    population = make_pop()
    joined = list(joiners.DistinctRandomTuples([population] * 2, ['population'] * 2))
    
    _gen = recombiners.PerGeneTuple(joined, per_indiv_rate=1.0, per_gene_rate=None)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    assert all(g1 is not g2 for g1, g2 in zip(population, offspring)), "DistinctRandom failed"
    assert all(g not in population for g in offspring), "Some individuals were not cloned"
    assert sum(g.statistic.get('recombined', 0) for g in offspring) == len(offspring), "Some individuals were not recombined"
    strikes = sum(len(set(g)) < 2 for g in offspring)
    print "stikes:", strikes
    assert strikes < 3, "Some individuals did not get two gene values"

def test_recombiners_PerGeneTuple_HalfFromFirst():
    population = make_pop()
    joined = list(joiners.DistinctRandomTuples([population] * 2, ['population'] * 2))
    
    _gen = recombiners.PerGeneTuple(joined, per_indiv_rate=1.0, per_gene_rate=0.5)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    assert all(g1 is not g2 for g1, g2 in zip(population, offspring)), "DistinctRandom failed"
    assert all(g not in population for g in offspring), "Some individuals were not cloned"
    assert sum(g.statistic.get('recombined', 0) for g in offspring) == len(offspring), "Some individuals were not recombined"
    strikes = sum(len(set(g)) < 2 for g in offspring)
    print "stikes:", strikes
    assert strikes < 3, "Some individuals did not get two gene values"
