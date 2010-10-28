import tests
from itertools import izip as zip, islice, chain
import esec.species.integer as integer

from esec.context import rand, notify

Species = integer.IntegerSpecies({ }, None)

def _print(pop):
    for i in pop:
        print i.phenome

def _make_pop(gen, **kwargs):
    pop = list(islice(gen(**kwargs), 10))
    assert len(pop) == 10, "length was not 10"
    print
    print ', '.join('%s=%s' % i for i in kwargs.iteritems())
    print '\n'.join(i.phenome_string for i in pop)
    assert all(isinstance(i, integer.IntegerIndividual) for i in pop), "not all individuals were correct type"
    return pop

def test_init():
    for gen, expected_genes in [
        (Species.init_random, set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])),
        (Species.init_low, set([0])),
        (Species.init_high, set([10])),
        (Species.init_toggle, set([0, 10])),
        (Species.init_increment, set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])),  # pop == 10, therefore no 10 gene
        (Species.init_count, set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])),      # pop == 10, therefore no 10 gene
        ]:
        
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
        (Species.mutate_random, {'per_indiv_rate': 1.0, 'per_gene_rate': 1.0}, set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])),
        (Species.mutate_delta, {'per_indiv_rate': 0.0, 'per_gene_rate': 0.0}, set([0])),
        (Species.mutate_delta, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.0}, set([0])),
        (Species.mutate_delta, {'per_indiv_rate': 0.0, 'per_gene_rate': 1.0}, set([0])),
        (Species.mutate_delta, {'per_indiv_rate': 1.0, 'per_gene_rate': 1.0}, set([0, 1])),
        (Species.mutate_delta, {'per_indiv_rate': 0.5, 'per_gene_rate': 1.0}, set([0, 1])),
        (Species.mutate_delta, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.5}, set([0, 1])),
        # per_indiv_rate defaults to 1.0
        (Species.mutate_delta, {'per_gene_rate': 1.0, 'step_size': 2, 'positive_rate': 1}, set([2])),
        (Species.mutate_delta, {'per_gene_rate': 1.0, 'step_size': 2, 'positive_rate': 0}, set([0])),
        (Species.mutate_delta, {'per_gene_rate': 1.0, 'step_size': 2, 'positive_rate': 0.5}, set([0, 2])),
        (Species.mutate_gaussian, {'per_indiv_rate': 0.0, 'per_gene_rate': 0.0}, set([0])),
        (Species.mutate_gaussian, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.0}, set([0])),
        (Species.mutate_gaussian, {'per_indiv_rate': 0.0, 'per_gene_rate': 1.0}, set([0])),
        (Species.mutate_gaussian, {'per_indiv_rate': 1.0, 'per_gene_rate': 1.0}, None),
        (Species.mutate_gaussian, {'per_indiv_rate': 0.5, 'per_gene_rate': 1.0}, None),
        (Species.mutate_gaussian, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.5}, None),
        ]:
        
        yield check_mutate, gen, params, expected_genes

def check_init_length_int(gen, expected_genes):
    pop = _make_pop(gen, length=10, lowest=0, highest=10)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_range_int(gen, expected_genes):
    pop = _make_pop(gen, shortest=5, longest=15, lowest=0, highest=10)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"
    
def check_init_length_dict_int(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5, 'max': 15, 'exact': 10}, lowest=0, highest=10)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_dict_range_int(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5, 'max': 15}, lowest=0, highest=10)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"

def check_init_length_float(gen, expected_genes):
    pop = _make_pop(gen, length=10.4, lowest=0.1, highest=10.3)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_range_float(gen, expected_genes):
    pop = _make_pop(gen, shortest=5.2, longest=15.7, lowest=0.1, highest=10.3)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"
    
def check_init_length_dict_float(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5.2, 'max': 15.7, 'exact': 10.4}, lowest=0.1, highest=10.3)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_dict_range_float(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5.2, 'max': 15.7}, lowest=0.1, highest=10.3)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"

def check_mutate(gen, params, expected_genes):
    pop = _make_pop(Species.init_low, length=10, lowest=0, highest=10)
    
    params['_source'] = iter(pop)
    
    pop2 = _make_pop(gen, **params)
    all_genes = set(chain(*(iter(i.genome) for i in pop2)))
    if expected_genes:
        assert all_genes == expected_genes, "%s != %s" % (all_genes, expected_genes)
    else:
        assert len(all_genes) > 1, "len(%s) <= 1" % all_genes
