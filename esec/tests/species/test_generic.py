import tests
from itertools import islice, chain
import esec.species.binary
import esec.species.integer
import esec.species.real

from esec.context import rand, notify

b_ind = esec.species.binary.BinaryIndividual
b_spec = esec.species.binary.BinarySpecies({ }, None)
i_ind = esec.species.integer.IntegerIndividual
i_spec = esec.species.integer.IntegerSpecies({ }, None)
r_ind = esec.species.real.RealIndividual
r_spec = esec.species.real.RealSpecies({ }, None)

def _print(pop):
    for i in pop:
        print i.phenome

def _make_pop(gen, expect, **kwargs):
    pop = list(islice(gen(**kwargs), 100))
    assert len(pop) == 100, "length was not 100"
    print
    print ', '.join('%s=%s' % i for i in kwargs.iteritems())
    print '\n'.join(i.phenome_string for i in pop)
    assert all(isinstance(i, expect) for i in pop), "not all individuals were correct type"
    return pop

def test_fixed_length_mutate():
    test_cases = [
            ('mutate_insert', {'per_indiv_rate': 0.0 }, [10, 10]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'length': 1 }, [11, 11]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'length': 5 }, [15, 15]),
            ('mutate_insert', {'per_indiv_rate': 0.5, 'length': 1 }, [10, 11]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'shortest': 1, 'longest': 5 }, [11, 15]),
            ('mutate_insert', {'per_indiv_rate': 0.5, 'shortest': 1, 'longest': 5 }, [10, 15]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'shortest': 1, 'longest': 5, 'longest_result': 12 }, [11, 12]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'shortest': 1.1, 'longest': 5.1, 'longest_result': 12.1 }, [11, 12]),

            ('mutate_delete', {'per_indiv_rate': 0.0 }, [10, 10]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'length': 1 }, [9, 9]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'length': 5 }, [5, 5]),
            ('mutate_delete', {'per_indiv_rate': 0.5, 'length': 1 }, [9, 10]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'shortest': 1, 'longest': 5 }, [5, 9]),
            ('mutate_delete', {'per_indiv_rate': 0.5, 'shortest': 1, 'longest': 5 }, [5, 10]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'shortest': 1, 'longest': 5, 'shortest_result': 8 }, [8, 9]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'shortest': 1.1, 'longest': 5.1, 'shortest_result': 8.1 }, [8, 9]),
    ]
    
    for pop_gen in [(lambda: _make_pop(b_spec.init_random, b_ind, length=10)),
                    (lambda: _make_pop(i_spec.init_random, i_ind, length=10)),
                    (lambda: _make_pop(r_spec.init_random, r_ind, length=10))]:
        for gen, params, expected_length in test_cases:
            yield check_mutate, pop_gen, gen, params, expected_length

def test_variable_length_mutate():
    test_cases = [
            ('mutate_insert', {'per_indiv_rate': 0.0 }, [5, 15]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'length': 1 }, [6, 16]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'length': 5 }, [10, 20]),
            ('mutate_insert', {'per_indiv_rate': 0.5, 'length': 1 }, [5, 16]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'shortest': 1, 'longest': 5 }, [6, 20]),
            ('mutate_insert', {'per_indiv_rate': 0.5, 'shortest': 1, 'longest': 5 }, [5, 20]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'shortest': 1, 'longest': 5, 'longest_result': 17 }, [6, 17]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'shortest': 1, 'longest': 5, 'longest_result': 12 }, [6, 15]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'length': 1.1 }, [6, 16]),
            ('mutate_insert', {'per_indiv_rate': 1.0, 'shortest': 1.1, 'longest': 5.1, 'longest_result': 12.1 }, [6, 15]),

            ('mutate_delete', {'per_indiv_rate': 0.0 }, [5, 15]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'length': 1 }, [4, 14]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'length': 5 }, [1, 10]),
            ('mutate_delete', {'per_indiv_rate': 0.5, 'length': 1 }, [4, 15]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'shortest': 1, 'longest': 5 }, [1, 14]),
            ('mutate_delete', {'per_indiv_rate': 0.5, 'shortest': 1, 'longest': 5 }, [1, 15]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'shortest': 1, 'longest': 5, 'shortest_result': 8 }, [5, 14]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'length': 1.1 }, [4, 14]),
            ('mutate_delete', {'per_indiv_rate': 1.0, 'shortest': 1.1, 'longest': 5.1, 'shortest_result': 8.1 }, [5, 14]),
    ]
    
    for pop_gen in [(lambda: _make_pop(b_spec.init_random, b_ind, shortest=5, longest=15)),
                    (lambda: _make_pop(i_spec.init_random, i_ind, shortest=5, longest=15)),
                    (lambda: _make_pop(r_spec.init_random, r_ind, shortest=5, longest=15))]:
        for gen, params, expected_length in test_cases:
            yield check_mutate, pop_gen, gen, params, expected_length

def check_mutate(pop_gen, gen, params, expected_length):
    pop = pop_gen()
    
    params['_source'] = iter(pop)
    
    pop2 = _make_pop(getattr(pop[0], gen), type(pop[0]), **params)
    
    if len(expected_length) == 2:
        l, h = expected_length
        assert all(l <= len(i) <= h for i in pop2), "!(%s <= len(i) <= %s)" % (l, h)
    else:
        assert all(len(i) in expected_length for i in pop2), "len(i) not in %s" % (expected_length,)
