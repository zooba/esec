from itertools import islice

from esec.species.integer import IntegerSpecies
from esec.species import JoinedSpecies
from esec.individual import JoinedIndividual
from esec.fitness import FitnessMaximise, FitnessMinimise

from esec.context import _context
import random
_context.rand = random.Random(10)
def FakeNotify(*p, **kw): print p, kw
_context.notify = FakeNotify

class TestEvaluatorMax(object):
    def eval(self, indiv):
        return FitnessMaximise(indiv[-1])

class TestEvaluatorMin(object):
    def eval(self, indiv):
        return FitnessMinimise(indiv[-1])

class TestJoinedEvaluator(object):
    def eval(self, indiv):
        return indiv[0].fitness

test_species_max = IntegerSpecies({ }, TestEvaluatorMax())
test_species_min = IntegerSpecies({ }, TestEvaluatorMin())
JoinedSpecies._eval_default = TestJoinedEvaluator()

def make_pop_max():
    _gen = test_species_max.init_count(length=10)
    return list(islice(_gen, 100))

def make_best_pop_max():
    _gen = test_species_max.init_high(length=10, highest=1000)
    return list(islice(_gen, 100))

def make_pop_variable_max():
    _gen = test_species_max.init_count(shortest=1, longest=100)
    return list(islice(_gen, 100))

def make_pop_min():
    _gen = test_species_min.init_count(length=10)
    return list(islice(_gen, 100))

def make_best_pop_min():
    _gen = test_species_min.init_low(length=10, highest=1000)
    return list(islice(_gen, 100))

def make_pop_variable_min():
    _gen = test_species_min.init_count(shortest=1, longest=100)
    return list(islice(_gen, 100))

