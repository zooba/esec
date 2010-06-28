from random import randrange
from esec.fitness import Fitness, EmptyFitness
from esec.individual import JoinedIndividual
from esec.species import JoinedSpecies
import esec.landscape.binary as binary

def test_inttobin():
    assert binary.inttobin(1, 4) == '0001' 
    assert binary.inttobin(15, 8) == '00001111' 
    assert binary.inttobin(255, 16) == '0000000011111111'   

def test_inttobinlist():
    assert binary.inttobinlist(1,4) == [0,0,0,1]
    assert binary.inttobinlist(15,8) == [0,0,0,0,1,1,1,1]    
    
def test_all_bvp():
    classes = [getattr(binary, n) for n in dir(binary)]
    classes = [c for c in classes if type(c) is type]
    classes = [c for c in classes if issubclass(c, binary.Binary) and c is not binary.Binary]
    for cls in classes:
        if cls not in (binary.NKC, binary.CNF_SAT, binary.ECC):
            yield check_bvp, cls
    
def check_bvp(cls):
    for cfg in cls.test_cfg:
        bvp = cls.by_cfg_str(cfg)
        # create a test individual (random binary list)
        param = [randrange(2) for _ in xrange(bvp.size.min)]
        # test list of random binary values
        fitness = bvp.eval(param)
        assert isinstance(fitness, (int, long, float, Fitness, EmptyFitness)), "Result was not fitness value"
        # create a test individual (random binary list)
        param = [randrange(2) for _ in xrange(bvp.size.max)]
        # test list of random binary values
        fitness = bvp.eval(param)
        assert isinstance(fitness, (int, long, float, Fitness, EmptyFitness)), "Result was not fitness value"
    # test print_info works
    print '\n'.join(bvp.info(5))
    #assert False
              
            
# Special features

def test_NKC():
    cls = binary.NKC
    for cfg in cls.test_cfg:
        bvp = cls.by_cfg_str(cfg)
        # create a test individual (random binary list)
        param = []
        for _ in xrange(bvp.group):
            param.append([randrange(2) for _ in xrange(bvp.size.exact)])
        # test list of random binary values
        fitness = bvp.eval(JoinedIndividual(param, [str(i) for i in xrange(bvp.group)], JoinedSpecies))
        assert isinstance(fitness, (int, long, float, Fitness, EmptyFitness)), "Result was not fitness value"
    print '\n'.join(bvp.info(5))
    #assert False

def test_CNF_SAT():
    bvp = binary.CNF_SAT.by_cfg_str('430 3 100 SAW')
    param = [randrange(2) for _ in xrange(bvp.size.min)]
    bvp.update_saw(param)
    param = [randrange(2) for _ in xrange(bvp.size.max)]
    bvp.update_saw(param)
    
def test_ECC():
    bvp = binary.ECC.by_cfg_str('3 4 1')
    assert bvp.size.exact == 6, 'param count (size.exact) is '+str(bvp.size.exact)
    codes = bvp._splitgenome([0,0,0,1,1,1])
    assert len(codes) == 4
    assert bvp.legal([0,0,0,1,1,1]) == False # compliment dist() == 0,
    assert bvp.legal([0,0,0,0,0,1]) == True
