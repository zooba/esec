import tests
from itertools import izip as zip, islice, chain
import esec.species.binary as binary

from esec.context import rand, notify

Species = binary.BinarySpecies({ }, None)

def _print(pop):
    for i in pop:
        print i.phenome

def _make_pop(gen, **kwargs):
    pop = list(islice(gen(**kwargs), 100))
    assert len(pop) == 100, "length was not 100"
    print
    print ', '.join('%s=%s' % i for i in kwargs.iteritems())
    print '\n'.join(i.phenome_string for i in pop)
    assert all(isinstance(i, binary.BinaryIndividual) for i in pop), "not all individuals were correct type"
    return pop

def test_init():
    for gen, expected_genes in [
        (Species.init_random, set([0, 1])),
        (Species.init_zero, set([0])),
        (Species.init_one, set([1])),
        (Species.init_toggle, set([0, 1]))]:
        
        yield check_init_length_int, gen, expected_genes
        yield check_init_length_range_int, gen, expected_genes
        yield check_init_length_dict_int, gen, expected_genes
        yield check_init_length_dict_range_int, gen, expected_genes
        
        yield check_init_length_float, gen, expected_genes
        yield check_init_length_range_float, gen, expected_genes
        yield check_init_length_dict_float, gen, expected_genes
        yield check_init_length_dict_range_float, gen, expected_genes
    
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
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'length': 10}, set([1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'length': 20}, set([1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 0.5, 'length': 10}, set([0, 1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 0.5, 'length': 20}, set([0, 1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'shortest': 10, 'longest': 10}, set([1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'shortest': 10, 'longest': 20}, set([1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'shortest': 2, 'longest': 5}, set([0, 1])),
        (Species.mutate_gap_inversion, {'per_indiv_rate': 1.0, 'shortest': 2, 'longest': 15}, set([0, 1])),
        ]:
        
        yield check_mutate, gen, params, expected_genes

def check_init_length_int(gen, expected_genes):
    pop = _make_pop(gen, length=10)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_range_int(gen, expected_genes):
    pop = _make_pop(gen, shortest=5, longest=15)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"
    
def check_init_length_dict_int(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5, 'max': 15, 'exact': 10})
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_dict_range_int(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5, 'max': 15})
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"

def check_init_length_float(gen, expected_genes):
    pop = _make_pop(gen, length=10.4)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_range_float(gen, expected_genes):
    pop = _make_pop(gen, shortest=5.2, longest=15.7)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"
    
def check_init_length_dict_float(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5.2, 'max': 15.7, 'exact': 10.4})
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_dict_range_float(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5.2, 'max': 15.7})
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"

def check_mutate(gen, params, expected_genes):
    pop = _make_pop(Species.init_zero, length=10)
    
    params['_source'] = iter(pop)
    
    pop2 = _make_pop(gen, **params)
    all_genes = set(chain(*(iter(i.genome) for i in pop2)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
