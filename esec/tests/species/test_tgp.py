import tests
from itertools import izip as zip
import esec.species.tgp as tgp

from esec.context import rand, notify

Species = tgp.TgpSpecies({ }, None)

def _make_bool_indiv(names):
    program = [ ]
    for n in names.split(' '):
        if n[0:2] == 'T#':
            program.append(tgp.Terminal(int(n[2:])))
        elif n == '(' or n == ')':
            pass
        else:
            program.append(getattr(Species, '_instr_bool_' + n))
    return program

def _cmp(source, expected):
    pop = [tgp.TgpIndividual([source], Species, instructions=Species.boolean_instructions, instruction_set='boolean', terminals=3)]
    new_pop = list(Species.mutate_edit(_source=pop))

    assert len(new_pop) == 1, "Expected one individual"
    indiv = new_pop[0]
    assert len(indiv) == 1, "Expected one program"
    program = indiv[0]
    assert len(program) == len(expected), "Length is incorrect. Expect %d, not %d" % (len(expected), len(program))
    print [type(p) for p in source]
    print [type(p) for p in program]
    print [type(p) for p in expected]
    print
    print [repr(p) for p in source]
    print [repr(p) for p in program]
    print [repr(p) for p in expected]
    for i, (g1, g2) in enumerate(zip(program, expected)):
        assert isinstance(g1, type(g2)), "Instructions at %d are not the same type. Expect %s, not %s" % (i, type(g2), type(g1))
        assert g1 == g2, "Instructions at %d are not equal. Expect %s, not %s" % (i, repr(g2), repr(g1))

def test_mutate_edit_notnot_1():
    # Test NOT NOT (trivial case)
    source = _make_bool_indiv('not not T#0')
    expected = _make_bool_indiv('T#0')
    
    _cmp(source, expected)

def test_mutate_edit_notnot_2():
    # Test NOT NOT (instructions before and after)
    source = _make_bool_indiv('and not not T#0 or T#1 T#0')
    expected = _make_bool_indiv('and T#0 or T#1 T#0')
    
    _cmp(source, expected)

def test_mutate_edit_notnot_3():
    # Test NOT NOT (with nestings)
    source = _make_bool_indiv('not not or T#0 T#1')
    expected = _make_bool_indiv('or T#0 T#1')
    
    _cmp(source, expected)

def test_mutate_edit_ifnot_1():
    # Test IF NOT (trivial case)
    source = _make_bool_indiv('if not T#0 T#2 T#1')
    expected = _make_bool_indiv('if T#0 T#1 T#2')
    
    _cmp(source, expected)

def test_mutate_edit_ifnot_2():
    # Test IF NOT (nested expression)
    source = _make_bool_indiv('if not ( and T#0 T#1 ) T#2 T#1')
    expected = _make_bool_indiv('if ( and T#0 T#1 ) T#1 T#2')
    
    _cmp(source, expected)

def test_mutate_edit_ifnot_3():
    # Test IF NOT (nested true)
    source = _make_bool_indiv('if not T#0 ( and T#1 T#2 ) T#1')
    expected = _make_bool_indiv('if T#0 T#1 ( and T#1 T#2 )')
    
    _cmp(source, expected)

def test_mutate_edit_ifnot_4():
    # Test IF NOT (nested false)
    source = _make_bool_indiv('if not T#0 T#1 ( and T#1 T#2 )')
    expected = _make_bool_indiv('if T#0 ( and T#1 T#2 ) T#1')
    
    _cmp(source, expected)

def test_mutate_edit_ifnot_5():
    # Test IF NOT (nested all)
    source = _make_bool_indiv('if not ( and T#0 T#1 ) ( and T#0 T#2 ) ( or T#0 T#1 )')
    expected = _make_bool_indiv('if ( and T#0 T#1 ) ( or T#0 T#1 ) ( and T#0 T#2 )')
    
    _cmp(source, expected)

