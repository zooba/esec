import tests
from itertools import islice, chain
import esec.species.sequence as sequence

from esec.context import rand, notify

Species = sequence.SequenceSpecies({ }, None)

def _print(pop):
    for i in pop:
        print i.phenome

def _make_pop(gen, **kwargs):
    pop = list(islice(gen(**kwargs), 100))
    assert len(pop) == 100, "length was not 100"
    print
    print ', '.join('%s=%s' % i for i in kwargs.iteritems())
    print '\n'.join(i.phenome_string for i in pop)
    assert all(isinstance(i, sequence.SequenceIndividual) for i in pop), "not all individuals were correct type"
    return pop

def test_init():
    genes = list(xrange(10))
    
    for gen, expected_genes in [
        (Species.init_random, set(genes)),
        (Species.init_forward, genes),
        (Species.init_reverse, list(reversed(genes))),
        ]:
        
        yield check_init_length_int, gen, expected_genes
        yield check_init_item_count_int, gen, expected_genes
        yield check_init_length_dict_int, gen, expected_genes
        
        yield check_init_length_float, gen, expected_genes
        yield check_init_item_count_float, gen, expected_genes
        yield check_init_length_dict_float, gen, expected_genes

def test_mutate():
    genes = list(xrange(10))
    for gen, params, expected_genes in [
        (Species.mutate_random, {'per_indiv_rate': 0.0, 'per_gene_rate': 0.0}, genes),
        (Species.mutate_random, {'per_indiv_rate': 1.0, 'per_gene_rate': 0.0}, genes),
        (Species.mutate_random, {'per_indiv_rate': 0.0, 'per_gene_rate': 1.0}, genes),
        (Species.mutate_random, {'per_indiv_rate': 1.0, 'per_gene_rate': 1.0}, None),
        ]:
        
        yield check_mutate, gen, params, expected_genes

def test_repair():
    for gen, params, expected_genes in [
        (Species.repair, {'sequentially': True}, None),
        (Species.repair, {'randomly': True}, None),
        ]:
        
        yield check_repair, gen, params, expected_genes

def check_init_length_int(gen, expected_genes):
    pop = _make_pop(gen, length=10)
    
    for genes in (i.genome for i in pop):
        assert len(genes) == 10, "not all individuals had 10 genes"
        assert type(expected_genes)(genes) == expected_genes, "%s != %s" % (genes, expected_genes)
    
    
def check_init_item_count_int(gen, expected_genes):
    pop = _make_pop(gen, item_count=10)
    
    for genes in (i.genome for i in pop):
        assert len(genes) == 10, "not all individuals had 10 genes"
        assert type(expected_genes)(genes) == expected_genes, "%s != %s" % (genes, expected_genes)
    
def check_init_length_dict_int(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5, 'max': 15, 'exact': 10})
    
    for genes in (i.genome for i in pop):
        assert len(genes) == 10, "not all individuals had 10 genes"
        assert type(expected_genes)(genes) == expected_genes, "%s != %s" % (genes, expected_genes)
    
def check_init_length_float(gen, expected_genes):
    pop = _make_pop(gen, length=10.4)
    
    for genes in (i.genome for i in pop):
        assert len(genes) == 10, "not all individuals had 10 genes"
        assert type(expected_genes)(genes) == expected_genes, "%s != %s" % (genes, expected_genes)
    
def check_init_item_count_float(gen, expected_genes):
    pop = _make_pop(gen, item_count=10.4)
    
    for genes in (i.genome for i in pop):
        assert len(genes) == 10, "not all individuals had 10 genes"
        assert type(expected_genes)(genes) == expected_genes, "%s != %s" % (genes, expected_genes)
    
def check_init_length_dict_float(gen, expected_genes):
    pop = _make_pop(gen, length={'min': 5.2, 'max': 15.7, 'exact': 10.4})
    
    for genes in (i.genome for i in pop):
        assert len(genes) == 10, "not all individuals had 10 genes"
        assert type(expected_genes)(genes) == expected_genes, "%s != %s" % (genes, expected_genes)
    
def check_mutate(gen, params, expected_genes):
    pop = _make_pop(Species.init_forward, length=10)
    
    params['_source'] = iter(pop)
    
    pop2 = _make_pop(gen, **params)
    for genes in (i.genome for i in pop2):
        if expected_genes:
            assert type(expected_genes)(genes) == expected_genes, "%s != %s" % (genes, expected_genes)
        else:
            assert len(set(genes)) == 10, "len(set(%s)) != 10" % genes

def check_repair(gen, params, expected_genes):
    pop = _make_pop(Species.init_random, length=10)
    pop2 = _make_pop(Species.crossover_one, _source=iter(pop), per_pair_rate=1.0)
    pop3 = _make_pop(gen, _source=iter(pop2), **params)
    
    for genes in (i.genome for i in pop3):
        if expected_genes:
            assert type(expected_genes)(genes) == expected_genes, "%s != %s" % (genes, expected_genes)
        else:
            assert len(set(genes)) == 10, "len(set(%s)) != 10" % genes
