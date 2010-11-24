import tests
from itertools import islice, chain
import esec.species.real as real

from esec.context import rand, notify

Species = real.RealSpecies({ }, None)

def _print(pop):
    for i in pop:
        print i.phenome

def _make_pop(gen, **kwargs):
    pop = list(islice(gen(**kwargs), 100))
    assert len(pop) == 100, "length was not 100"
    print
    print ', '.join('%s=%s' % i for i in kwargs.iteritems())
    print '\n'.join(i.phenome_string for i in pop)
    assert all(isinstance(i, real.RealIndividual) for i in pop), "not all individuals were correct type"
    return pop

def test_init():
    for gen, expected_genes in [
        (Species.init_random, [0, 1]),
        (Species.init_low, [0, 0]),
        (Species.init_high, [1, 1]),
        (Species.init_toggle, [0, 1]),
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
        (Species.mutate_random, {'per_indiv_rate': 0.0, 'per_gene_rate': 0.0}, [0, 0]),
        (Species.mutate_random, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.0}, [0, 0]),
        (Species.mutate_random, {'per_indiv_rate': 0.0, 'per_gene_rate': 1.0}, [0, 0]),
        (Species.mutate_random, {'per_indiv_rate': 1.0, 'per_gene_rate': 1.0}, [0, 1]),
        (Species.mutate_delta, {'per_indiv_rate': 0.0, 'per_gene_rate': 0.0}, [0, 0]),
        (Species.mutate_delta, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.0}, [0, 0]),
        (Species.mutate_delta, {'per_indiv_rate': 0.0, 'per_gene_rate': 1.0}, [0, 0]),
        (Species.mutate_delta, {'per_indiv_rate': 1.0, 'per_gene_rate': 1.0}, [0, 1]),
        (Species.mutate_delta, {'per_indiv_rate': 0.5, 'per_gene_rate': 1.0}, [0, 1]),
        (Species.mutate_delta, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.5}, [0, 1]),
        # per_indiv_rate defaults to 1.0
        (Species.mutate_delta, {'per_gene_rate': 1.0, 'step_size': 0.1, 'positive_rate': 1}, [0.1, 0.1]),
        (Species.mutate_delta, {'per_gene_rate': 1.0, 'step_size': 0.1, 'positive_rate': 0}, [0, 0]),
        (Species.mutate_delta, {'per_gene_rate': 1.0, 'step_size': 0.1, 'positive_rate': 0.5}, [0, 0.1]),
        (Species.mutate_gaussian, {'per_indiv_rate': 0.0, 'per_gene_rate': 0.0}, [0, 0]),
        (Species.mutate_gaussian, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.0}, [0, 0]),
        (Species.mutate_gaussian, {'per_indiv_rate': 0.0, 'per_gene_rate': 1.0}, [0, 0]),
        (Species.mutate_gaussian, {'per_indiv_rate': 1.0, 'per_gene_rate': 1.0}, [0, 1]),
        (Species.mutate_gaussian, {'per_indiv_rate': 0.5, 'per_gene_rate': 1.0}, [0, 1]),
        (Species.mutate_gaussian, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.5}, [0, 1]),
        ]:
        
        yield check_mutate, gen, params, expected_genes

def check_init_length_int(gen, expected_genes):
    pop = _make_pop(gen, length=10, lowest=0.0, highest=1.0)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    l, h = expected_genes
    assert all(l <= i <= h for i in all_genes), "!(%s <= %s <= %s)" % (l, all_genes, h)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_range_int(gen, expected_genes):
    pop = _make_pop(gen, shortest=5, longest=15, lowest=0.0, highest=1.0)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    l, h = expected_genes
    assert all(l <= i <= h for i in all_genes), "!(%s <= %s <= %s)" % (l, all_genes, h)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"
    
def check_init_length_dict_int(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5, 'max': 15, 'exact': 10}, lowest=0.0, highest=1.0)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    l, h = expected_genes
    assert all(l <= i <= h for i in all_genes), "!(%s <= %s <= %s)" % (l, all_genes, h)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_dict_range_int(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5, 'max': 15}, lowest=0.0, highest=1.0)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    l, h = expected_genes
    assert all(l <= i <= h for i in all_genes), "!(%s <= %s <= %s)" % (l, all_genes, h)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"

def check_init_length_float(gen, expected_genes):
    pop = _make_pop(gen, length=10.4, lowest=0.0, highest=1.0)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    l, h = expected_genes
    assert all(l <= i <= h for i in all_genes), "!(%s <= %s <= %s)" % (l, all_genes, h)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_range_float(gen, expected_genes):
    pop = _make_pop(gen, shortest=5.2, longest=15.7, lowest=0.0, highest=1.0)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    l, h = expected_genes
    assert all(l <= i <= h for i in all_genes), "!(%s <= %s <= %s)" % (l, all_genes, h)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"
    
def check_init_length_dict_float(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5.2, 'max': 15.7, 'exact': 10.4}, lowest=0.0, highest=1.0)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    l, h = expected_genes
    assert all(l <= i <= h for i in all_genes), "!(%s <= %s <= %s)" % (l, all_genes, h)
    
    assert all(len(i.genome) == 10 for i in pop), "not all individuals had 10 genes"
    
def check_init_length_dict_range_float(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5.2, 'max': 15.7},lowest=0.0, highest=1.0)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop)))
    l, h = expected_genes
    assert all(l <= i <= h for i in all_genes), "!(%s <= %s <= %s)" % (l, all_genes, h)
    
    assert all(5 <= len(i.genome) <= 15 for i in pop), "not all individuals had [5,15] genes"

def check_mutate(gen, params, expected_genes):
    pop = _make_pop(Species.init_low, length=10, lowest=0.0, highest=1.0)
    
    params['_source'] = iter(pop)
    
    pop2 = _make_pop(gen, **params)
    
    all_genes = set(chain(*(iter(i.genome) for i in pop2)))
    l, h = expected_genes
    assert all(l <= i <= h for i in all_genes), "!(%s <= %s <= %s)" % (l, all_genes, h)
