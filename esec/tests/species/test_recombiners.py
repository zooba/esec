from tests import *
from itertools import izip
from esec.context import rand
from esec.generators import joiners
from esec.individual import OnIndividual

make_pop = make_pop_max
make_pop_variable = make_pop_variable_max

def test_recombiners_Uniform_Values():
    population = make_pop()
    
    _gen = OnIndividual('crossover_uniform')(_source=iter(population), two_children=True)
    child1, child2 = next(_gen), next(_gen)
    print "len(child1) = %d, len(child2) = %d, len(population[0]) = %d" % (len(child1), len(child2), len(population[0]))
    assert len(child1) == len(child2) == len(population[0]), "Individual's length was changed"
    child1_set, child2_set = set(child1.genome), set(child2.genome)
    print "len(set(child1)) = %d, len(set(child2)) = %d" % (len(child1_set), len(child2_set))
    assert len(child1_set) == len(child2_set) == 2, "Number of distinct values is not 2"
    print "set(child1) = %s" % child1_set
    print "set(child2) = %s" % child2_set
    assert child1_set == child2_set, "Distinct values are not matched"

def test_recombiners_Uniform_Selection_All():
    population = make_pop()
    
    _gen = OnIndividual('crossover_uniform')(_source=iter(population), two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "intersection = %s" % set(offspring).intersection(set(population))
    assert len(set(offspring).intersection(set(population))) == 0, "Did not modify some individuals"

def test_recombiners_Uniform_Selection_None():
    population = make_pop()
    
    _gen = OnIndividual('crossover_uniform')(_source=iter(population), per_pair_rate=0.0, two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "difference = %s" % set(offspring).difference(set(population))
    assert len(set(offspring).difference(set(population))) == 0, "Did not modify any individuals"

def test_recombiners_Uniform_Selection_Half():
    population = make_pop_variable(shortest=4)
    
    modify_count = 0
    for _ in xrange(100):
        _gen = OnIndividual('crossover_uniform')(_source=iter(population), per_pair_rate=0.5, two_children=True)
        offspring = list(_gen)
        assert len(offspring) == len(population), "Did not select all individuals"
        modify_count += len(set(offspring).difference(set(population)))
    modify_rate = float(modify_count) / (100.0 * len(population))
    assert 0.4 <= modify_rate <= 0.6, "Did not modify approximately 50% of individuals"

def test_recombiners_Discrete_Values():
    population = make_pop()
    
    _gen = OnIndividual('crossover_discrete')(_source=iter(population), two_children=True)
    children = list(_gen)
    child1, child2 = children[0:2]
    print "len(child1) = %d, len(child2) = %d, len(population[0]) = %d" % (len(child1), len(child2), len(population[0]))
    assert len(child1) == len(child2) == len(population[0]), "Individual's length was changed"
    print '\n'.join(str(set(child)) for child in children)
    assert not all(len(set(child)) != 2 for child in children), "Number of distinct values is not 2"
    child1_set, child2_set = set(child1.genome), set(child2.genome)
    print "set(child1) = %s" % child1_set
    print "set(child2) = %s" % child2_set
    assert child1_set == child2_set, "Distinct values are not matched"

def test_recombiners_Discrete_Selection_All():
    population = make_pop()
    
    _gen = OnIndividual('crossover_discrete')(_source=iter(population), two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "intersection = %s" % set(offspring).intersection(set(population))
    assert len(set(offspring).intersection(set(population))) == 0, "Did not modify some individuals"

def test_recombiners_Discrete_Selection_None():
    population = make_pop()
    
    _gen = OnIndividual('crossover_discrete')(_source=iter(population), per_pair_rate=0.0, two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "difference = %s" % set(offspring).difference(set(population))
    assert len(set(offspring).difference(set(population))) == 0, "Did not modify any individuals"

def test_recombiners_Discrete_Selection_Half():
    population = make_pop_variable(shortest=4)
    
    modify_count = 0
    for _ in xrange(100):
        _gen = OnIndividual('crossover_discrete')(_source=iter(population), per_pair_rate=0.5, two_children=True)
        offspring = list(_gen)
        assert len(offspring) == len(population), "Did not select all individuals"
        modify_count += len(set(offspring).difference(set(population)))
    modify_rate = float(modify_count) / (100.0 * len(population))
    assert 0.4 <= modify_rate <= 0.6, "Did not modify approximately 50% of individuals"


def test_recombiners_SingleSame_Values():
    population = make_pop()
    
    _gen = OnIndividual('crossover_one')(_source=iter(population), two_children=True)
    child1, child2 = next(_gen), next(_gen)
    print "len(child1) = %d, len(child2) = %d, len(population[0]) = %d" % (len(child1), len(child2), len(population[0]))
    assert len(child1) == len(child2) == len(population[0]), "Individual's length was changed"
    child1_set, child2_set = set(child1.genome), set(child2.genome)
    print "len(set(child1)) = %d, len(set(child2)) = %d" % (len(child1_set), len(child2_set))
    assert len(child1_set) == len(child2_set) == 2, "Number of distinct values is not 2"
    print "set(child1) = %s" % child1_set
    print "set(child2) = %s" % child2_set
    assert child1_set == child2_set, "Distinct values are not matched"

def test_recombiners_SingleSame_Selection_All():
    population = make_pop()
    
    _gen = OnIndividual('crossover_one')(_source=iter(population), two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "intersection = %s" % set(offspring).intersection(set(population))
    assert len(set(offspring).intersection(set(population))) == 0, "Did not modify some individuals"

def test_recombiners_SingleSame_Selection_None():
    population = make_pop()
    
    _gen = OnIndividual('crossover_one')(_source=iter(population), per_pair_rate=0.0, two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "difference = %s" % set(offspring).difference(set(population))
    assert len(set(offspring).difference(set(population))) == 0, "Did not modify any individuals"

def test_recombiners_SingleSame_Selection_Half():
    population = make_pop_variable(shortest=4)
    
    modify_count = 0
    for _ in xrange(100):
        _gen = OnIndividual('crossover_one')(_source=iter(population), per_pair_rate=0.5, two_children=True)
        offspring = list(_gen)
        assert len(offspring) == len(population), "Did not select all individuals"
        modify_count += len(set(offspring).difference(set(population)))
    modify_rate = float(modify_count) / (100.0 * len(population))
    assert 0.4 <= modify_rate <= 0.6, "Did not modify approximately 50% of individuals"

def test_recombiners_SingleDifferent_Values():
    population = make_pop_variable(shortest=4)
    
    _gen = OnIndividual('crossover_one_different')(_source=iter(population), two_children=True)
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

def test_recombiners_SingleDifferent_Selection_All():
    population = make_pop_variable(shortest=4)
    
    _gen = OnIndividual('crossover_different')(_source=iter(population), points=1, two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "intersection = %s" % set(offspring).intersection(set(population))
    assert len(set(offspring).intersection(set(population))) == 0, "Did not modify some individuals"
    
    _gen = OnIndividual('crossover_different')(_source=iter(population), points=2, two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "intersection = %s" % set(offspring).intersection(set(population))
    assert len(set(offspring).intersection(set(population))) == 0, "Did not modify some individuals"

def test_recombiners_SingleDifferent_Selection_None():
    population = make_pop_variable(shortest=4)
    
    _gen = OnIndividual('crossover_one_different')(_source=iter(population), per_pair_rate=0.0, two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "difference = %s" % set(offspring).difference(set(population))
    assert len(set(offspring).difference(set(population))) == 0, "Modified some individuals"

def test_recombiners_SingleDifferent_Selection_Half():
    population = make_pop_variable(shortest=4)
    
    modify_count = 0
    for _ in xrange(100):
        _gen = OnIndividual('crossover_one_different')(_source=iter(population), per_pair_rate=0.5, two_children=True)
        offspring = list(_gen)
        assert len(offspring) == len(population), "Did not select all individuals"
        modify_count += len(set(offspring).difference(set(population)))
    modify_rate = float(modify_count) / (100.0 * len(population))
    assert 0.4 <= modify_rate <= 0.6, "Did not modify approximately 50% of individuals"

def test_recombiners_Segmented_None():
    population = make_pop()
    _gen = OnIndividual('crossover_segmented')(_source=iter(population), per_pair_rate=0.0, two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "difference = %s" % set(offspring).difference(set(population))
    assert len(set(offspring).difference(set(population))) == 0, "Modified some individuals"

def test_recombiners_Segmented_NoSegments():
    population = make_pop()
    _gen = OnIndividual('crossover_segmented')(_source=iter(population), per_pair_rate=1.0, switch_rate=0.0, two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "difference = %s" % set(offspring).difference(set(population))
    assert len(set(offspring).difference(set(population))) == 0, "Modified some individuals"

def test_recombiners_Segmented_Normal():
    population = make_pop()
    _gen = OnIndividual('crossover_segmented')(_source=iter(population), per_pair_rate=1.0, switch_rate=0.9, two_children=True)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    print "intersection = %s" % set(offspring).intersection(set(population))
    assert len(set(offspring).intersection(set(population))) == 0, "Did not modify some individuals"
    
    for indiv in offspring:
        distinct_genes = set(indiv.genome)
        if len(distinct_genes) != 2: print indiv.genome
        assert len(distinct_genes) == 2, "Did not cross individuals"

def test_recombiners_PerGeneTuple_None():
    population = make_pop()
    joined = list(joiners.DistinctRandomTuples(_source=[population] * 2))
    
    _gen = OnIndividual('crossover_tuple')(_source=iter(joined), per_indiv_rate=1.0, greediness=1.0)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    assert all(g1 is g2 for g1, g2 in izip(population, offspring)), "Did not return first individual"

def test_recombiners_PerGeneTuple_NotFromFirst():
    population = make_pop()
    joined = list(joiners.DistinctRandomTuples(_source=[population] * 2))
    
    _gen = OnIndividual('crossover_tuple')(_source=iter(joined), per_indiv_rate=1.0, greediness=0.0)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    assert all(g1 is not g2 for g1, g2 in izip(population, offspring)), "DistinctRandom failed"
    assert all(g not in population for g in offspring), "Some individuals were not cloned"
    assert sum(g.statistic.get('recombined', 0) for g in offspring) == len(offspring), "Some individuals were not recombined"

def test_recombiners_PerGeneTuple_AutoProb():
    population = make_pop()
    joined = list(joiners.DistinctRandomTuples(_source=[population] * 2))
    
    _gen = OnIndividual('crossover_tuple')(_source=iter(joined), per_indiv_rate=1.0, greediness=None)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individuals"
    assert all(g1 is not g2 for g1, g2 in izip(population, offspring)), "DistinctRandom failed"
    assert all(g not in population for g in offspring), "Some individuals were not cloned"
    assert sum(g.statistic.get('recombined', 0) for g in offspring) == len(offspring), "Some individuals were not recombined"
    strikes = sum(len(set(g)) < 2 for g in offspring)
    print "stikes:", strikes
    assert strikes < 3, "Some individuals did not get two gene values"
