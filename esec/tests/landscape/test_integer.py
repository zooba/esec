from random import randrange
from itertools import izip as zip
from esec.fitness import Fitness, EmptyFitness
import esec.landscape.integer as integer

    
def test_all_ivp():
    classes = [getattr(integer, n) for n in dir(integer)]
    classes = [c for c in classes if type(c) is type]
    classes = [c for c in classes if issubclass(c, integer.Integer) and c is not integer.Integer]
    for cls in classes:
        yield check_ivp, cls
    
def check_ivp(cls):
    for cfg in cls.test_cfg:
        ivp = cls.by_cfg_str(cfg)
        # create a test individual (random binary list)
        param = [randrange(lower, upper) for lower, upper in zip(*ivp.bounds)]
        # test list of random integer values
        fitness = ivp.eval(param)
        assert isinstance(fitness, (int, long, float, Fitness, EmptyFitness)), "Result was not fitness value"
        if ivp.size.min < ivp.size.max:
            # create a test individual (random binary list)
            param = param[:ivp.size.min]
            # test list of random integer values
            fitness = ivp.eval(param)
            assert isinstance(fitness, (int, long, float, Fitness, EmptyFitness)), "Result was not fitness value"
        # test print_info works
        print '\n'.join(ivp.info(5))
        
    # if legal test, create illegal case
    for t in cls.test_legal:
        print "Legal test:", t
        assert ivp.legal(t) == True, "Test value is not legal"
    for t in cls.test_illegal:
        print "Illegal test:", t
        assert ivp.legal(t) == False, "Test value is not illegal"
    
    
