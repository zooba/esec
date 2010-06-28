from random import uniform
from esec.fitness import Fitness, EmptyFitness
import esec.landscape.real as real

    
def test_all_rvp():
    classes = [getattr(real, n) for n in dir(real)]
    classes = [c for c in classes if type(c) is type]
    classes = [c for c in classes if issubclass(c, real.Real) and c is not real.Real]
    for cls in classes:
        yield check_rvp, cls
    
def check_rvp(cls):
    print '=== Testing %s ===' % cls.__name__
    for cfg in cls.test_cfg:
        rvp = cls.by_cfg_str(cfg)
        # create a test individual (random real list)
        #lbd = rvp.lbd if type(rvp.lbd) is list else [rvp.lbd] * rvp.size.max
        #ubd = rvp.ubd if type(rvp.ubd) is list else [rvp.ubd] * rvp.size.max
        
        param = [uniform(lower, upper) for lower, upper in zip(*rvp.bounds)]
        # test list of random real values
        fitness = rvp.eval(param)
        assert isinstance(fitness, (int, long, float, Fitness, EmptyFitness)), "Result was not fitness value"
        if rvp.size.min < rvp.size.max:
            # create a test individual (random real list)
            param = param[:rvp.size.min]
            # test list of random real values
            fitness = rvp.eval(param)
            assert isinstance(fitness, (int, long, float, Fitness, EmptyFitness)), "Result was not fitness value"
    # test print_info works
    print '\n'.join(rvp.info(5))
        
