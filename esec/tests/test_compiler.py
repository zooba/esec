from esec.compiler import Compiler
import traceback

def test_hide_nested():
    # test each bracket/quote type
    source = 'A (B) C [D] E {F} G "H" I \'J\' K'
    expected = 'A ( ) C [ ] E { } G " " I \' \' K'
    actual = Compiler._hide_nested(source)
    print "Source:   %s\nExpected: %s\nActual:   %s\n" % (source, expected, actual)
    assert actual == expected
    print
    
    # test simple nested brackets
    source = 'A (B [C] {D}) E'
    expected = 'A (         ) E'
    actual = Compiler._hide_nested(source)
    print "Source:   %s\nExpected: %s\nActual:   %s\n" % (source, expected, actual)
    assert actual == expected
    print
    
    # test complex nested brackets
    source = 'A (B [C (D "E)" ) F ] G ) H'
    expected = 'A (                     ) H'
    actual = Compiler._hide_nested(source)
    print "Source:   %s\nExpected: %s\nActual:   %s\n" % (source, expected, actual)
    assert actual == expected
    print

def test_cross_split():
    # Simple sanity test
    source1 = 'A,B,C,D,E'
    source2 = '_,___,___'
    separator = ','
    expected = ['A', 'B,C', 'D,E']
    actual = list(Compiler._cross_split(source1, source2, separator))
    print "Source 1: %s\nSource 2: %s\nExpected: %s\nActual:   %s\n" % (source1, source2, expected, actual)
    assert actual == expected

def test_cross_search():
    # Simple sanity test
    source1 = 'ABCDEFGHIJKLMN'
    source2 = '_____111______'
    pattern = '1+'
    expected = 'FGH'
    actual = Compiler._cross_search(source1, pattern, source2)
    print "Source 1: %s\nSource 2: %s\nExpected: %s\nActual:   %s\n" % (source1, source2, expected, actual)
    assert actual == expected

def test_Compiler():
    
    # Create objects sufficient to imitate both ConfigDict and Individual without
    # importing them.
    class _TestObj(object):
        def __str__(self): return 'TestObject'
        
        def __getattr__(self, name):
            if name == 'size': return 5
            if name == 'rate': return 0.1
            if name in ('selection', 'type', 'init', 'merge'): return self.type_iter
            return self
        
        def type_iter(self, src=None, rate=0.0, per_gene_rate=0.0):
            if src:
                for s in src: yield s
            else:
                while True: yield _TestIndiv()
    
    class _TestIndiv(object):
        def born(self): return self
        def __str__(self): return 'TestIndividual'
        @property
        def fitness(self): return 0
        @fitness.setter
        def fitness(self, value): pass
        @fitness.deleter
        def fitness(self): pass
    
    class _TestMonitor(object):
        def on_yield(self, name, group): pass
    
    
    def _NullGenerator(src, *p, **kw):
        return iter(src)
    def _NullInitialiser(*p, **kw):
        while True: yield _TestIndiv()
    
    context = {
        'cfg' : _TestObj(),
        '_monitor' : _TestMonitor(),
        '_group' : list,
        '_on_yield': lambda name, group: None,
        'random_int': _NullInitialiser,
        'tournament': _NullGenerator,
        'crossover_one': _NullGenerator,
        'mutate_random': _NullGenerator,
        'uniform_random': _NullGenerator,
        'mutate_delta': _NullGenerator,
        'best': _NullGenerator,
        'worst': _NullGenerator,
    }
    
    
    # Compile sample code
    c = Compiler('''
            FROM random_int SELECT 50 population_A, 50 population_B, 50 population_C
            YIELD population_A, population_B, population_C
            
            # Initialise list of islands (using a Python list)
            `islands = [population_A, population_B, population_C]
            
            BEGIN generation
              FROM population_A SELECT 50 offspring USING tournament(k=3)
              FROM offspring    SELECT population_A USING crossover_one, mutate_random(per_gene_rate=0.05)

              FROM population_B SELECT 50 offspring USING uniform_random
              FROM offspring    SELECT population_B USING mutate_delta(step_size=1.0)

              FROM population_C SELECT 10 offspring USING best
              FROM offspring    SELECT offspring USING crossover_one, mutate_random(per_gene_rate=0.2)
              FROM population_C, offspring SELECT 50 population_C USING best

              REPEAT 3
                src = rand.choice(islands)
                dest = rand.choice(islands)
                # Python code to ensure source and destination islands are different
                `while dest is src:
                `    dest = rand.choice(islands)
                    
                FROM src  SELECT 5 travellers, stay_at_home USING best
                FROM dest SELECT 5 losers, survivors USING worst
                FROM travellers, survivors SELECT dest
                FROM losers, stay_at_home  SELECT src
              END repeat

              YIELD population_A, population_B, population_C
            END generation''')
    
    succeeded = True

    c.context = context
    c.compile()
    #context = ContextDict(c.context)
    context = c.context
    
    # Some header helpers
    def hdr0(s): return '%s\n%s\n%s' % ('*' * len(s), s, '*' * len(s))
    def hdr1(s): return s + '\n' + '=' * len(s)
    def hdr2(s): return s + '\n' + '-' * len(s)
    
    # Display results
    print hdr0("  Compiler Test Results  ")
    print
    print hdr1(" Source Code ")
    print c.source_code
    print
    print hdr1(" Reset Code ")
    print c.reset
    print
    print hdr2("  Exec Results  ")
    try:
        exec c.reset in context
        print '      Pass'
    except:
        print ''.join(traceback.format_exc())
        succeeded = False
    print
    print hdr1(" Breed Code ")
    print c.breed
    print
    print hdr2("  Exec Results  ")
    try:
        exec c.breed in context
        print '      Pass'
    except:
        print ''.join(traceback.format_exc())
        succeeded = False
    print
    print hdr1(" Context ")
    def disp(v):
        if isinstance(v, list): return '[ %s ... {%d} ]' % (v[0], len(v)) if v else '[ ]'
        elif isinstance(v, tuple): return '( %s ... {%d} )' % (v[0], len(v)) if v else '( )'
        elif isinstance(v, dict): return '{ %s: %s ... {%d} }' % (v.items()[0] + (len(v),)) if v else '{ }'
        else: return str(v)
    print '\n'.join(('%-20s: %s' % (k,disp(v)) for k,v in context.items()))

    assert succeeded
