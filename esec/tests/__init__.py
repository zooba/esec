from esec.species.integer import IntegerSpecies
from esec.species import JoinedSpecies
from esec.individual import JoinedIndividual

class TestEvaluator(object):
    def eval(self, indiv):
        return indiv[-1]

class TestJoinedEvaluator(object):
    def eval(self, indiv):
        return indiv[0].fitness

test_species = IntegerSpecies({ }, TestEvaluator())
JoinedSpecies._eval_default = TestJoinedEvaluator()

def make_pop():
    _gen = test_species.init_count(length=10)
    return [next(_gen) for _ in xrange(100)]

def make_best_pop():
    _gen = test_species.init_high(length=10, highest=1000)
    return [next(_gen) for _ in xrange(100)]

def make_pop_variable():
    _gen = test_species.init_count(shortest=1, longest=100)
    return [next(_gen) for _ in xrange(100)]
