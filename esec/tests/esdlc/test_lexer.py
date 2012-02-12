from esdlc.ast.lexer import Token, tokenise

def test_Token():
    t1 = Token('tag', 'value', 0, 1)
    t2 = Token('tag', 'value', 0, 1)
    
    assert t1 == t2
    
    t2.value = 'value B'
    
    assert t1 != t2
    
    # greater/less than only check line/column
    assert not t1 > t2
    assert not t1 < t2
    
    t2.col = 3
    assert t1 < t2
    assert t2 > t1
    
    print str(t1)
    assert str(t1) == 'value (1:2)'
    
    print repr(t1)
    assert repr(t1) == '<tag>value (1:2)'

def test_tokenise_number():
    source = "0 0.0 1. 1.2 1e2 2.e1 3.4e7 1e-4 1e+4 3.2e-2 4.4e+3"
    values = [0.0, 0.0, 1.0, 1.2, 100.0, 20.0, 34000000.0, 0.0001, 10000.0, 0.032, 4400.0]
    tokens = tokenise(source)
    
    print tokens
    assert tokens[-1].tag == 'eos'
    tokens = tokens[:-1]
    
    assert len(tokens) == len(values)
    assert all(t.tag == 'number' for t in tokens)
    
    actual = [float(t.value) for t in tokens]
    print actual
    print values
    assert actual == values

def test_tokenise_constant():
    source = "true TRUE True false FALSE False none NONE None null NULL Null"
    values = ['true', 'true', 'true', 'false', 'false', 'false', 'none', 'none', 'none', 'null', 'null', 'null']
    tokens = tokenise(source)
    
    print tokens
    assert tokens[-1].tag == 'eos'
    tokens = tokens[:-1]
    
    assert len(tokens) == len(values)
    assert all(t.tag == 'name' for t in tokens)
    
    actual = [t.value for t in tokens]
    print actual
    print values
    assert actual == values

def test_tokenise_comment():
    sources = [
        r"name # comment # comment ; comment // comment \ not a separator",
        r"name ; comment # comment ; comment // comment \ not a separator",
        r"name // comment # comment ; comment // comment \ not a separator",
    ]
    for source in sources:
        comment = source[5:]
        tokens = tokenise(source)
        
        print tokens
        assert [t.tag for t in tokens] == ['name', 'comment', 'eos']
        
        assert tokens[1].value == comment

def check_tags(source, expect):
    tokens = tokenise(source)
    
    print tokens
    assert [t.tag for t in tokens] == expect.split()

def test_tokenise_commands():
    yield check_tags, \
        "from FROM select SELECT using USING join JOIN into INTO yield YIELD begin " + \
        "BEGIN repeat REPEAT end END eval EVAL evaluate EVALUATE", \
        "name "*22 + "eos"
    
def test_tokenise_continue():
    yield check_tags, \
        "name 2.3 \\ \n name 4.6", \
        "name number name number eos"

def test_tokenise_line_ending():
    yield check_tags, \
        'name \n  name \r\n name \r\r\n  name \r  name', \
        'name eos name eos  name eos eos name eos name eos'
    
    yield check_tags, \
        'name \n  name \r \n   name \r\r \n     name \n\r    name', \
        'name eos name eos eos name eos eos eos name eos eos name eos'
    
    yield check_tags, \
        '', \
        'eos'
    
def test_tokenise_operator():
    yield check_tags, \
        '+ - * / % ^ ( ) { } [ ] = . , +-*/%^(){}[]=.,', \
        ('operator '*6 + 'open close '*3 + 'assign operator comma ')*2 + 'eos'
    
    # each of these should be separate operators
    yield check_tags, \
        '+-+ -+- -- ++ *- ^- %+', \
        'operator '*16 + 'eos'

def test_tokenise_equation():
    yield check_tags, \
        'y = (-b + sqrt(b^2 - 4*a*c)) / (2 * a)', \
        'name assign open operator name operator name open name operator number operator number ' + \
        'operator name operator name close close operator open number operator name close eos'

def test_tokenise_functioncall():
    yield check_tags, \
        'class.method(param=value,   param = value[index+2],         param =   2.3 )', \
        'name operator name open name assign name comma name assign name open name operator number ' + \
        'close comma name assign number close eos'

CODE = r'''FROM random_real(length=cfg.length,lowest=-2.0,highest=2.0) SELECT (size) population
YIELD population

BEGIN GENERATION
    # Stochastic Universal Sampling for bases
    FROM population SELECT (size) bases USING fitness_sus(mu=size)
    
    # Ensure r0 != r1 != r2, but any may equal i
    JOIN bases, population, population INTO mutators USING random_tuples(distinct=true)
    
    FROM mutators SELECT mutants USING mutate_DE(scale=F)
    
    JOIN targets, mutants INTO target_mutant_pairs USING tuples
    FROM target_mutant_pairs SELECT trials USING \
         crossover_tuple(per_gene_rate=CR[2])
    
    JOIN targets, trials INTO targets_trial_pairs USING tuples
    FROM targets_trial_pairs SELECT population USING best_of_tuple
    
    YIELD population
END GENERATION'''

CODE_TOKENS = [
    'name name open name assign name operator name comma name assign operator number comma name assign number close ' + \
        'name open name close name eos',
    'name name eos',
    'eos',
    'name name eos',
    'comment eos',
    'name name name open name close name name name open name assign name close eos',
    'eos',
    'comment eos',
    'name name comma name comma name name name name name open name assign name close eos',
    'eos',
    'name name name name name name open name assign name close eos',
    'eos',
    'name name comma name name name name name eos',
    'name name name name name name open name assign name open number close close eos',
    'eos',
    'name name comma name name name name name eos',
    'name name name name name name eos',
    'eos',
    'name name eos',
    'name name eos',
]

CODE_VALUES = [
    'from random_real ( length = cfg . length , lowest = - 2.0 , highest = 2.0 ) select ( size ) population',
    'yield population',
    '',
    'begin generation',
    '# Stochastic Universal Sampling for bases',
    'from population select ( size ) bases using fitness_sus ( mu = size )',
    '',
    '# Ensure r0 != r1 != r2, but any may equal i',
    'join bases , population , population into mutators using random_tuples ( distinct = true )',
    '',
    'from mutators select mutants using mutate_de ( scale = f )',
    '',
    'join targets , mutants into target_mutant_pairs using tuples',
    'from target_mutant_pairs select trials using crossover_tuple ( per_gene_rate = cr [ 2 ] )',
    '',
    'join targets , trials into targets_trial_pairs using tuples',
    'from targets_trial_pairs select population using best_of_tuple',
    '',
    'yield population',
    'end generation',
]

def split_at_eos(src):
    result = []
    for i in src:
        result.append(i)
        if i.tag == 'eos':
            yield result
            result = []
            

def test_tokenise():
    lines = list(split_at_eos(tokenise(CODE)))
    
    print len(lines), len(CODE_TOKENS)
    assert len(lines) == len(CODE_TOKENS)
    
    for i_raw, j in zip(lines, CODE_TOKENS):
        i = ' '.join(t.tag for t in i_raw)
        print i
        print j
        assert i == j
    
    for i_raw, j in zip(lines, CODE_VALUES):
        i = ' '.join(str(t.value) for t in i_raw[:-1])
        print i
        print j
        assert i == j
    
if __name__ == '__main__':
    funcs = [(k, v) for k, v in globals().items() if k.startswith('test_') and hasattr(v, '__call__')]
    for fname, f in funcs:
        print fname
        gen = f()
        if gen:
            for t in gen:
                print t
                t[0](*t[1:])
