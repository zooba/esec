import tests
from itertools import islice, chain
import esec.species.binary_int as binary

from esec.context import rand, notify

Species = binary.BinaryIntegerSpecies({ }, None)

def _print(pop):
    for i in pop:
        print i.phenome

def _make_pop(gen, **kwargs):
    pop = list(islice(gen(**kwargs), 100))
    assert len(pop) == 100, "length was not 100"
    print
    print ', '.join('%s=%s' % i for i in kwargs.iteritems())
    print '\n'.join(''.join(str(i) for i in indiv.genome) for indiv in pop)
    assert all(isinstance(i, binary.BinaryIntegerIndividual) for i in pop), "not all individuals were correct type"
    return pop

def test_init():
    for gen, expected_genes in [
        (Species.init_random_int, set([0, 1])),
        ]:
        
        yield check_init_length_int, gen, expected_genes
        yield check_init_length_dict_int, gen, expected_genes
        
        yield check_init_length_float, gen, expected_genes
        yield check_init_length_dict_float, gen, expected_genes
    
def test_mutate():
    for gen, params, expected_genes in [
        (Species.mutate_random, {'per_indiv_rate': 0.0, 'per_gene_rate': 0.0}, set([0])),
        (Species.mutate_random, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.0}, set([0])),
        (Species.mutate_random, {'per_indiv_rate': 0.0, 'per_gene_rate': 1.0}, set([0])),
        (Species.mutate_random, {'per_indiv_rate': 1.0, 'per_gene_rate': 1.0}, set([0, 1])),
        (Species.mutate_bitflip, {'per_indiv_rate': 0.0, 'per_gene_rate': 0.0}, set([0])),
        (Species.mutate_bitflip, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.0}, set([0])),
        (Species.mutate_bitflip, {'per_indiv_rate': 0.0, 'per_gene_rate': 1.0}, set([0])),
        (Species.mutate_bitflip, {'per_indiv_rate': 1.0, 'per_gene_rate': 1.0}, set([1])),
        (Species.mutate_bitflip, {'per_indiv_rate': 0.5, 'per_gene_rate': 1.0}, set([0, 1])),
        (Species.mutate_bitflip, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.5}, set([0, 1])),
        (Species.mutate_inversion, {'per_indiv_rate': 0.0}, set([0])),
        (Species.mutate_inversion, {'per_indiv_rate': 0.5}, set([0, 1])),
        (Species.mutate_inversion, {'per_indiv_rate': 1.0}, set([1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 0.0}, set([0])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'length': 80}, set([1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'length': 100}, set([1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 0.5, 'length': 80}, set([0, 1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 0.5, 'length': 100}, set([0, 1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'shortest': 80, 'longest': 80}, set([1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'shortest': 80, 'longest': 100}, set([1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'shortest': 50, 'longest': 80}, set([0, 1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'shortest': 50, 'longest': 100}, set([0, 1])),
        ]:
        
        yield check_mutate, gen, params, expected_genes

def test_mapping():
    for gen, genes, expected in [
        (Species.ones_complement_mapping, [[0, 0, 0, 0]], [0]),
        (Species.ones_complement_mapping, [[0, 0, 0, 1]], [1]),
        (Species.ones_complement_mapping, [[0, 0, 1, 0]], [2]),
        (Species.ones_complement_mapping, [[0, 1, 0, 0]], [4]),
        (Species.ones_complement_mapping, [[1, 0, 0, 0]], [8]),
        (Species.ones_complement_mapping, [[1, 0, 0, 1]], [9]),
        (Species.ones_complement_mapping, [[1, 0, 1, 1]], [11]),
        (Species.ones_complement_mapping, [[1, 1, 1, 1]], [15]),
        
        (Species.twos_complement_mapping, [[1, 0, 0, 0]], [-8]),
        (Species.twos_complement_mapping, [[1, 0, 0, 1]], [-7]),
        (Species.twos_complement_mapping, [[1, 0, 1, 1]], [-5]),
        (Species.twos_complement_mapping, [[1, 1, 1, 1]], [-1]),
        (Species.twos_complement_mapping, [[0, 0, 0, 0]], [0]),
        (Species.twos_complement_mapping, [[0, 0, 0, 1]], [1]),
        (Species.twos_complement_mapping, [[0, 0, 1, 0]], [2]),
        (Species.twos_complement_mapping, [[0, 1, 0, 0]], [4]),
        (Species.twos_complement_mapping, [[0, 1, 1, 1]], [7]),
        
        (Species.gray_code_mapping, [[0, 0, 0, 0]], [0]),
        (Species.gray_code_mapping, [[0, 0, 0, 1]], [1]),
        (Species.gray_code_mapping, [[0, 0, 1, 1]], [2]),
        (Species.gray_code_mapping, [[0, 0, 1, 0]], [3]),
        (Species.gray_code_mapping, [[0, 1, 1, 0]], [4]),
        (Species.gray_code_mapping, [[0, 1, 1, 1]], [5]),
        (Species.gray_code_mapping, [[0, 1, 0, 1]], [6]),
        (Species.gray_code_mapping, [[0, 1, 0, 0]], [7]),
        (Species.gray_code_mapping, [[1, 1, 0, 0]], [8]),
        (Species.gray_code_mapping, [[1, 1, 0, 1]], [9]),
        (Species.gray_code_mapping, [[1, 1, 1, 1]], [10]),
        (Species.gray_code_mapping, [[1, 1, 1, 0]], [11]),
        (Species.gray_code_mapping, [[1, 0, 1, 0]], [12]),
        (Species.gray_code_mapping, [[1, 0, 1, 1]], [13]),
        (Species.gray_code_mapping, [[1, 0, 0, 1]], [14]),
        (Species.gray_code_mapping, [[1, 0, 0, 0]], [15]),
        
        (Species.count_mapping, [[0, 0, 0, 0]], [0]),
        (Species.count_mapping, [[0, 0, 0, 1]], [1]),
        (Species.count_mapping, [[0, 0, 1, 0]], [1]),
        (Species.count_mapping, [[0, 1, 0, 0]], [1]),
        (Species.count_mapping, [[1, 0, 0, 0]], [1]),
        (Species.count_mapping, [[1, 0, 0, 1]], [2]),
        (Species.count_mapping, [[1, 0, 1, 1]], [3]),
        (Species.count_mapping, [[1, 1, 1, 1]], [4]),
        ]:
        
        yield check_mapping, gen, genes, expected
    
def check_mapping(gen, genes, expected):
    actual = list(gen(genes))
    
    print 'Actual:   ' + ', '.join(str(i) for i in actual)
    print 'Expected: ' + ', '.join(str(i) for i in expected)
    assert actual == expected
    
    actual = list(gen(genes * 5))
    
    print 'Actual:   ' + ', '.join(str(i) for i in actual)
    print 'Expected: ' + ', '.join(str(i) for i in expected * 5)
    assert actual == expected * 5

def check_init_length_int(gen, expected_genes):
    pop = _make_pop(gen, length=10, bits_per_value=8)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 80 for i in pop), "not all individuals had 80 genes"
    assert all(len(i.phenome) == 10 for i in pop), "not all individuals had 10 values"
    
def check_init_length_dict_int(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5, 'max': 15, 'exact': 10}, bits_per_value=8)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 80 for i in pop), "not all individuals had 80 genes"
    assert all(len(i.phenome) == 10 for i in pop), "not all individuals had 10 values"
    
def check_init_length_float(gen, expected_genes):
    pop = _make_pop(gen, length=10.4, bits_per_value=8.2)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 80 for i in pop), "not all individuals had 80 genes"
    assert all(len(i.phenome) == 10 for i in pop), "not all individuals had 10 values"
    
def check_init_length_dict_float(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5.2, 'max': 15.7, 'exact': 10.4}, bits_per_value=8.2)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 80 for i in pop), "not all individuals had 80 genes"
    assert all(len(i.phenome) == 10 for i in pop), "not all individuals had 10 values"
    
def check_mutate(gen, params, expected_genes):
    pop = _make_pop(Species.init_zero_int, length=10)
    
    params['_source'] = iter(pop)
    
    pop2 = _make_pop(gen, **params)
    all_genes = set(chain(*(iter(i.genome) for i in pop2)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
