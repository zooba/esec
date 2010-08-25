from . import *
import random
from esec.generators import selectors, joiners

rand = random

def notify(sender, name, param): pass
import __builtin__
__builtin__.rand = rand
__builtin__.notify = notify

def test_selectors_All():
    population = make_pop()
    
    _gen = selectors.All(iter(population))
    offspring = [next(_gen) for _ in xrange(50)]
    print "len(offspring) = %d, expected = 50" % len(offspring)
    assert len(offspring) == 50, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.All(iter(population))
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
def test_selectors_Best():
    population = make_pop()
    
    _gen = selectors.Best(iter(population))
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    print ['[fit=%s]' % i.fitness for i in offspring]
    print
    print ['[fit=%s]' % i.fitness for i in population]
    print
    assert all((i==j for i,j in zip(offspring, reversed(population[-10:])))), "Did not select correct individuals"
    
    _gen = selectors.Best(iter(population), only=True)
    offspring = [next(_gen) for _ in xrange(10)]
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all((i==population[-1] for i in offspring)), "Did not select best individual"
    
def test_selectors_Worst():
    population = make_pop()
    
    _gen = selectors.Worst(iter(population))
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all((i==j for i,j in zip(offspring, population[:10]))), "Did not select correct individuals"
    
    _gen = selectors.Worst(iter(population), only=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all((i==population[0] for i in offspring)), "Did not select worst individual"
    
def test_selectors_Tournament_2():
    population = make_pop()
    
    _gen = selectors.Tournament(iter(population), 2, replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.Tournament(iter(population), 2, replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.values[0] for i in offspring]
    print "fit[:50] = %d, fit[50:] = %d" % (sum(fit[:50]), sum(fit[50:]))
    assert sum(fit[:50]) > sum(fit[50:]), "Average fitness is not better in early selections"

def test_selectors_Tournament_3():
    population = make_pop()
    
    _gen = selectors.Tournament(iter(population), 3, replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.Tournament(iter(population), 3, replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.values[0] for i in offspring]
    print "fit[:50] = %d, fit[50:] = %d" % (sum(fit[:50]), sum(fit[50:]))
    assert sum(fit[:50]) > sum(fit[50:]), "Average fitness is not better in early selections"

def test_selectors_Tournament_5():
    population = make_pop()
    
    _gen = selectors.Tournament(iter(population), 5, replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.Tournament(iter(population), 5, replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.values[0] for i in offspring]
    print "fit[:50] = %d, fit[50:] = %d" % (sum(fit[:50]), sum(fit[50:]))
    assert sum(fit[:50]) > sum(fit[50:]), "Average fitness is not better in early selections"
    
def test_selectors_UniformRandom():
    population = make_pop()
    
    _gen = selectors.UniformRandom(iter(population), replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.UniformRandom(iter(population), replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    
def test_selectors_FitnessProportional():
    population = make_pop()
    
    _gen = selectors.FitnessProportional(iter(population), replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.FitnessProportional(iter(population), replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.values[0] for i in offspring]
    print "fit[:50] = %d, fit[50:] = %d" % (sum(fit[:50]), sum(fit[50:]))
    assert sum(fit[:50]) > sum(fit[50:]), "Average fitness is not better in early selections"
    
def test_selectors_RankProportional():
    population = make_pop()
    
    _gen = selectors.RankProportional(iter(population), replacement=True)
    offspring = [next(_gen) for _ in xrange(10)]
    print "len(offspring) = %d, expected = 10" % len(offspring)
    assert len(offspring) == 10, "Did not select expected number of individuals"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    
    _gen = selectors.RankProportional(iter(population), replacement=False)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
    assert len(set(offspring)) == len(offspring), "Individuals are not all unique"
    fit = [i.fitness.values[0] for i in offspring]
    print "fit[:50] = %d, fit[50:] = %d" % (sum(fit[:50]), sum(fit[50:]))
    assert sum(fit[:50]) > sum(fit[50:]), "Average fitness is not better in early selections"
    
def test_selectors_BestOfTuple():
    population = make_best_pop()
    population2 = make_pop()

    _gen = joiners.DistinctRandomTuples([population, population2, population2], ['population', 'pop2', 'pop2'])
    _gen = selectors.BestOfTuple(_gen)
    offspring = list(_gen)
    print "len(offspring) = %d, len(population) = %d" % (len(offspring), len(population))
    assert len(offspring) == len(population), "Did not select all individials"
    assert all([i in population for i in offspring]), "Some individuals not in original population"
