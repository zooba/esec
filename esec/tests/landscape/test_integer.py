from random import randrange
from itertools import izip
from esec.fitness import Fitness, EmptyFitness
import esec.landscape.integer as integer
from esec.species.integer import IntegerIndividual, IntegerSpecies
species = IntegerSpecies({ }, lambda _: 0)

def test_all_ivp():
    classes = [getattr(integer, n) for n in dir(integer)]
    classes = [c for c in classes if type(c) is type]
    classes = [c for c in classes if issubclass(c, integer.Integer) and c is not integer.Integer]
    for cls in classes:
        yield check_ivp, cls
    
def check_ivp(cls):
    for cfg in cls.test_cfg:
        ivp = cls.by_cfg_str(cfg)
        # create a test individual
        param = IntegerIndividual([randrange(lower, upper) 
                                   for lower, upper in izip(ivp.lower_bounds, ivp.upper_bounds)],
                                  lower_bounds=ivp.lower_bounds, upper_bounds=ivp.upper_bounds,
                                  parent=species)
        # test list of random integer values
        fitness = ivp.eval(param)
        assert isinstance(fitness, (int, long, float, Fitness, EmptyFitness)), "Result was not fitness value"
        if ivp.size.min < ivp.size.max:
            # create a test individual (random binary list)
            param = IntegerIndividual(param.genome[:ivp.size.min], parent=param)
            # test list of random integer values
            fitness = ivp.eval(param)
            assert isinstance(fitness, (int, long, float, Fitness, EmptyFitness)), "Result was not fitness value"
        # test print_info works
        print '\n'.join(ivp.info(5))
        
    # if legal test, create illegal case
    for t in cls.test_legal:
        print "Legal test:", t
        indiv = IntegerIndividual(t,
                                  lower_bounds=ivp.lower_bounds, upper_bounds=ivp.upper_bounds,
                                  parent=species)
        indiv._eval = ivp
        assert indiv.legal(), "Test value is not legal"
    for t in cls.test_illegal:
        print "Illegal test:", t
        indiv = IntegerIndividual(t,
                                  lower_bounds=ivp.lower_bounds, upper_bounds=ivp.upper_bounds,
                                  parent=species)
        indiv._eval = ivp
        assert not indiv.legal(), "Test value is not illegal"
    
