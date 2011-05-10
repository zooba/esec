from esdlc.ast.lexer import Token, tokenise

def test_Token():
    t1 = Token('tag', 'type', 'value', 0, 1)
    t2 = Token('tag', 'type', 'value', 0, 1)
    
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
    assert tokens[-1].tag == 'EOS'
    tokens = tokens[:-1]
    
    assert len(tokens) == len(values)
    assert all(t.tag == 'NUMBER' for t in tokens)
    
    actual = [float(t.value) for t in tokens]
    print actual
    print values
    assert actual == values

def test_tokenise_constant():
    source = "true TRUE True false FALSE False none NONE None null NULL Null"
    values = ['true', 'true', 'true', 'false', 'false', 'false', 'none', 'none', 'none', 'null', 'null', 'null']
    tokens = tokenise(source)
    
    print tokens
    assert tokens[-1].tag == 'EOS'
    tokens = tokens[:-1]
    
    assert len(tokens) == len(values)
    assert all(t.type == 'literal' for t in tokens)
    
    actual = [t.value.lower() for t in tokens]
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
        assert [t.tag for t in tokens] == ['NAME', 'COMMENTS', 'EOS']
        
        assert tokens[1].value == comment

def check_tags(source, expect):
    tokens = tokenise(source)
    
    print tokens
    assert [t.tag for t in tokens] == expect.split()

def test_tokenise_commands():
    yield check_tags, \
        "from FROM select SELECT using USING join JOIN into INTO yield YIELD begin " + \
        "BEGIN repeat REPEAT end END eval EVAL evaluate EVALUATE", \
        "FROM FROM SELECT SELECT USING USING JOIN JOIN INTO INTO YIELD YIELD BEGIN " + \
        "BEGIN REPEAT REPEAT END END EVAL EVAL EVAL EVAL EOS"
    
def test_tokenise_continue():
    yield check_tags, \
        "name 2.3 \\ \n name 4.6", \
        "NAME NUMBER NAME NUMBER EOS"

def test_tokenise_line_ending():
    yield check_tags, \
        'name \n  name \r\n name \r\r\n  name \r  name', \
        'NAME EOS NAME EOS  NAME EOS EOS NAME EOS NAME EOS'
    
    yield check_tags, \
        'name \n  name \r \n   name \r\r \n     name \n\r    name', \
        'NAME EOS NAME EOS EOS NAME EOS EOS EOS NAME EOS EOS NAME EOS'
    
    yield check_tags, \
        '', \
        'EOS'
    
def test_tokenise_operator():
    yield check_tags, \
        '+ - * / % ^ ( ) { } [ ] = . , +-*/%^(){}[]=.,', \
        'ADD SUB MUL DIV MOD POW OPEN_PAR CLOSE_PAR OPEN_BRACE CLOSE_BRACE OPEN_BRACKET CLOSE_BRACKET ASSIGN DOT COMMA ' + \
        'ADD SUB MUL DIV MOD POW OPEN_PAR CLOSE_PAR OPEN_BRACE CLOSE_BRACE OPEN_BRACKET CLOSE_BRACKET ASSIGN DOT COMMA EOS'
    
    # each of these should be separate operators
    yield check_tags, \
        '+-+ -+- -- ++ *- ^- %+', \
        'ADD SUB ADD SUB ADD SUB SUB SUB ADD ADD MUL SUB POW SUB MOD ADD EOS'

def test_tokenise_equation():
    yield check_tags, \
        'y = (-b + sqrt(b^2 - 4*a*c)) / (2 * a)', \
        'NAME ASSIGN OPEN_PAR SUB NAME ADD NAME OPEN_PAR NAME POW NUMBER SUB NUMBER MUL NAME MUL NAME ' + \
            'CLOSE_PAR CLOSE_PAR DIV OPEN_PAR NUMBER MUL NAME CLOSE_PAR EOS'

def test_tokenise_functioncall():
    yield check_tags, \
        'class.method(param=value,   param = value[index+2],         param =   2.3 )', \
        'NAME DOT NAME OPEN_PAR NAME ASSIGN NAME COMMA NAME ASSIGN NAME OPEN_BRACKET NAME ADD NUMBER ' + \
            'CLOSE_BRACKET COMMA NAME ASSIGN NUMBER CLOSE_PAR EOS'

CODE = r'''FROM random_real(length=cfg.length,lowest=-2.0,highest=2.0) SELECT (size) population
YIELD population

BEGIN GENERATION
    targets = population
    
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
    'FROM NAME OPEN_PAR NAME ASSIGN NAME DOT NAME COMMA NAME ASSIGN SUB NUMBER COMMA NAME ASSIGN NUMBER CLOSE_PAR ' + \
        'SELECT OPEN_PAR NAME CLOSE_PAR NAME EOS',
    'YIELD NAME EOS',
    'EOS',
    'BEGIN NAME EOS',
    'NAME ASSIGN NAME EOS',
    'EOS',
    'COMMENTS EOS',
    'FROM NAME SELECT OPEN_PAR NAME CLOSE_PAR NAME USING NAME OPEN_PAR NAME ASSIGN NAME CLOSE_PAR EOS',
    'EOS',
    'COMMENTS EOS',
    'JOIN NAME COMMA NAME COMMA NAME INTO NAME USING NAME OPEN_PAR NAME ASSIGN TRUE CLOSE_PAR EOS',
    'EOS',
    'FROM NAME SELECT NAME USING NAME OPEN_PAR NAME ASSIGN NAME CLOSE_PAR EOS',
    'EOS',
    'JOIN NAME COMMA NAME INTO NAME USING NAME EOS',
    'FROM NAME SELECT NAME USING NAME OPEN_PAR NAME ASSIGN NAME OPEN_BRACKET NUMBER CLOSE_BRACKET CLOSE_PAR EOS',
    'EOS',
    'JOIN NAME COMMA NAME INTO NAME USING NAME EOS',
    'FROM NAME SELECT NAME USING NAME EOS',
    'EOS',
    'YIELD NAME EOS',
    'END NAME EOS',
]

CODE_VALUES = [
    'FROM random_real ( length = cfg . length , lowest = - 2.0 , highest = 2.0 ) SELECT ( size ) population',
    'YIELD population',
    '',
    'BEGIN GENERATION',
    'targets = population',
    '',
    '# Stochastic Universal Sampling for bases',
    'FROM population SELECT ( size ) bases USING fitness_sus ( mu = size )',
    '',
    '# Ensure r0 != r1 != r2, but any may equal i',
    'JOIN bases , population , population INTO mutators USING random_tuples ( distinct = true )',
    '',
    'FROM mutators SELECT mutants USING mutate_DE ( scale = F )',
    '',
    'JOIN targets , mutants INTO target_mutant_pairs USING tuples',
    'FROM target_mutant_pairs SELECT trials USING crossover_tuple ( per_gene_rate = CR [ 2 ] )',
    '',
    'JOIN targets , trials INTO targets_trial_pairs USING tuples',
    'FROM targets_trial_pairs SELECT population USING best_of_tuple',
    '',
    'YIELD population',
    'END GENERATION',
]

def split_at_eos(src):
    result = []
    for i in src:
        result.append(i)
        if i.tag == 'EOS':
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
