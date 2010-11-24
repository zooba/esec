from tests import *
from itertools import izip
from esec.context import rand, notify
from esec.generators import selectors, joiners

def test_selectors_max():
    population = make_pop_max()
    yield check_selectors_All, population
    yield check_selectors_Best_max, population
    yield check_selectors_Worst_max, population
    yield check_selectors_Tournament_2, population
    yield check_selectors_Tournament_3, population
    yield check_selectors_Tournament_5, population
    yield check_selectors_UniformRandom, population
    yield check_selectors_UniformShuffle, population
    yield check_selectors_FitnessProportional, population
    yield check_selectors_FitnessProportionalSUS, population
    yield check_selectors_RankProportional, population
    yield check_selectors_RankProportionalSUS, population
    yield check_selectors_BestOfTuple, population, make_best_pop_max()
    
def test_selectors_min():
    population = make_pop_min()
    yield check_selectors_All, population
    yield check_selectors_Best_min, population
    yield check_selectors_Worst_min, population
    yield check_selectors_Tournament_2, population
    yield check_selectors_Tournament_3, population
    yield check_selectors_Tournament_5, population
    yield check_selectors_UniformRandom, population
    yield check_selectors_UniformShuffle, population
    yield check_selectors_FitnessProportional, population
    yield check_selectors_FitnessProportionalSUS, population
    yield check_selectors_RankProportional, population
    yield check_selectors_RankProportionalSUS, population
    yield check_selectors_BestOfTuple, population, make_best_pop_min()
    

def check_selectors_All(population):
    _gen = selectors.All(_source=iter(population))
    offspring = [next(_gen) for _ in xrange(50)]
    print "len(offspring) = %d, expected = 50" % len(offspring)
    assert len(offspring) == 50, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.All(_source=iter(population))
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
def check_selectors_Best_max(population):
    _gen = selectors.Best(_source=iter(population))
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    print ['[fit=%s]' % i.fitness for i in offspring]
    print
    print ['[fit=%s]' % i.fitness for i in population]
    print
    assert all((i==j for i,j in izip(offspring, reversed(population[-10:])))), "Did not select correct individuals"
    
    _gen = selectors.Best(_source=iter(population), only=True)
    offspring = [next(_gen) for _ in xrange(10)]
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all((i==population[-1] for i in offspring)), "Did not select best individual"

def check_selectors_Best_min(population):
    _gen = selectors.Best(_source=iter(population))
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    print ['[fit=%s]' % i.fitness for i in offspring]
    print
    print ['[fit=%s]' % i.fitness for i in population]
    print
    assert all((i==j for i,j in izip(offspring, population[:10]))), "Did not select correct individuals"
    
    _gen = selectors.Best(_source=iter(population), only=True)
    offspring = [next(_gen) for _ in xrange(10)]
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all((i==population[0] for i in offspring)), "Did not select best individual"

def check_selectors_Worst_max(population):
    _gen = selectors.Worst(_source=iter(population))
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all((i==j for i,j in izip(offspring, population[:10]))), "Did not select correct individuals"

    _gen = selectors.Worst(_source=iter(population), only=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all((i==population[0] for i in offspring)), "Did not select worst individual"

def check_selectors_Worst_min(population):
    _gen = selectors.Worst(_source=iter(population))
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all((i==j for i,j in izip(offspring, reversed(population[-10:])))), "Did not select correct individuals"

    _gen = selectors.Worst(_source=iter(population), only=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all((i==population[-1] for i in offspring)), "Did not select worst individual"

def check_selectors_Tournament_2(population):
    _gen = selectors.Tournament(_source=iter(population), k=2, replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.Tournament(_source=iter(population), k=2, replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.simple for i in offspring]
    print "fit[:50] = %d, fit[50:] = %d" % (sum(fit[:50]), sum(fit[50:]))
    assert sum(fit[:50]) > sum(fit[50:]), "Average fitness is not better in early selections"

def check_selectors_Tournament_3(population):
    _gen = selectors.Tournament(_source=iter(population), k=3, replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.Tournament(_source=iter(population), k=3, replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.simple for i in offspring]
    print "fit[:50] = %d, fit[50:] = %d" % (sum(fit[:50]), sum(fit[50:]))
    assert sum(fit[:50]) > sum(fit[50:]), "Average fitness is not better in early selections"

def check_selectors_Tournament_5(population):
    _gen = selectors.Tournament(_source=iter(population), k=5, replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.Tournament(_source=iter(population), k=5, replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.simple for i in offspring]
    print "fit[:50] = %d, fit[50:] = %d" % (sum(fit[:50]), sum(fit[50:]))
    assert sum(fit[:50]) > sum(fit[50:]), "Average fitness is not better in early selections"
    
def check_selectors_UniformRandom(population):
    _gen = selectors.UniformRandom(_source=iter(population), replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
def check_selectors_UniformShuffle(population):
    _gen = selectors.UniformRandom(_source=iter(population), replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    
def check_selectors_FitnessProportional(population):
    _gen = selectors.FitnessProportional(_source=iter(population), replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.FitnessProportional(_source=iter(population), replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.simple for i in offspring]
    print "fit[:50] = %d, fit[-50:] = %d" % (sum(fit[:50]), sum(fit[-50:]))
    assert sum(fit[:50]) > sum(fit[-50:]), "Average fitness is not better in early selections (INTERMITTENT)"
    
def check_selectors_FitnessProportionalSUS(population):
    _gen = selectors.FitnessProportionalSUS(_source=iter(population), mu=20)
    offspring = [next(_gen) for _ in xrange(20)]
    print "len(offspring) = %d, expected = 20" % len(offspring)
    assert len(offspring) == 20, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    gaps = [abs(i2.fitness.simple - i1.fitness.simple) for i1, i2 in izip(offspring[::2], offspring[1::2])]
    print ', '.join(str(i) for i in gaps)
    assert gaps[0] < gaps[-1], "Gaps between selections do not increase"
    
    _gen = selectors.FitnessProportionalSUS(_source=iter(population))
    offspring = [next(_gen) for _ in xrange(len(population))]
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    fit = [i.fitness.simple for i in offspring]
    print "fit[:50] = %d, fit[-50:] = %d" % (sum(fit[:50]), sum(fit[-50:]))
    assert sum(fit[:50]) > sum(fit[-50:]), "Average fitness is not better in early selections (INTERMITTENT)"
    
def check_selectors_RankProportional(population):
    _gen = selectors.RankProportional(_source=iter(population), expectation=2.0, replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.RankProportional(_source=iter(population), expectation=2.0, replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.simple for i in offspring]
    print "fit[:50] = %d, fit[-50:] = %d" % (sum(fit[:50]), sum(fit[-50:]))
    assert sum(fit[:50]) > sum(fit[-50:]), "Average fitness is not better in early selections (INTERMITTENT)"
    
def check_selectors_RankProportionalSUS(population):
    _gen = selectors.RankProportionalSUS(_source=iter(population), mu=20, expectation=2.0)
    offspring = [next(_gen) for _ in xrange(20)]
    print "len(offspring) = %d, expected = 20" % len(offspring)
    assert len(offspring) == 20, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    gaps = [abs(i2.fitness.simple - i1.fitness.simple) for i1, i2 in izip(offspring[::2], offspring[1::2])]
    print ', '.join(str(i) for i in gaps)
    assert gaps[0] < gaps[-1], "Gaps between selections do not increase"
    
    _gen = selectors.RankProportionalSUS(_source=iter(population), expectation=2.0)
    offspring = [next(_gen) for _ in xrange(len(population))]
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    fit = [i.fitness.simple for i in offspring]
    print "fit[:50] = %d, fit[-50:] = %d" % (sum(fit[:50]), sum(fit[-50:]))
    assert sum(fit[:50]) > sum(fit[-50:]), "Average fitness is not better in early selections (INTERMITTENT)"
    
def check_selectors_BestOfTuple(population, best_population):
    _gen = joiners.DistinctRandomTuples(_source=([best_population, population, population],
                                                 ['best_population', 'population', 'population']))
    _gen = selectors.BestOfTuple(_source=_gen)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(best_population))
    assert len(offspring) == len(best_population), "Did not select all individials"
    assert all([i in best_population for i in offspring]), "Some individuals not in original population"
