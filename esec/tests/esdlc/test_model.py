from esdlc.model.components import *

def parse_RPN(code):
    '''Constructs an arithmetic model from reverse-Polish notation.
    
    Supported operators are ``+-*/^%~``, where ``~`` is the unary ``-``
    operator.
    '''
    stack = []
    variables = {}
    for token in code.split(' '):
        if not token:
            continue
        if len(token) == 1 and token in '+-*/^%':
            right = stack.pop()
            left = stack.pop()
            stack.append(BinaryOp(left, token, right))
        elif token == '~':
            right = stack.pop()
            stack.append(UnaryOp('-', right))
        else:
            try:
                value = float(token)
                stack.append(VariableRef(Variable(value=value, constant=True)))
            except ValueError:
                var = variables.get(token)
                if not var: var = variables[token] = Variable(name=token)
                stack.append(VariableRef(var))
    return stack[0]

def check_operations(code, expected, vars):
    root = parse_RPN(code)
    actual = root.execute(dict(vars))
    assert actual == expected, "Expected %s; actual %s" % (expected, actual)

def test_arithmetic():
    for code, expected, vars in [
        ('10 20 +', 30, {}),
        ('20 10 -', 10, {}),
        ('10 20 *', 200, {}),
        ('20 10 /', 2, {}),
        ('10  2 ^', 100, {}),
        (' 2 10 %', 2, {}),
        ('20 10 ~ +', 10, {}),
        ('1 2 + 3 * 4 / 5 -', -2.75, {}),
    ]:
        yield check_operations, code, expected, vars

def test_variables():
    for code, expected, vars in [
        ('a b +', 30, {'a':10, 'b':20}),
        ('b a -', 10, {'a':10, 'b':20}),
        ('a b *', 200, {'a':10, 'b':20}),
        ('b a /', 2, {'a':10, 'b':20}),
        ('a c ^', 100, {'a':10, 'c':2}),
        ('c a %', 2, {'a':10, 'c':2}),
        ('b a ~ +', 10, {'a':10, 'b':20}),
        ('a b + c * d / e -', -2.75, {'a':1.0, 'b':2.0, 'c':3.0, 'd':4.0, 'e':5.0}),
        ('a a + a a + + a +', 5, {'a':1}),
    ]:
        yield check_operations, code, expected, vars

def test_generator():
    def int_counter(length):
        i = 0
        while True:
            yield [i] * length
            i += 1

    gen = Variable('int_counter', external=True)
    grp = Variable('population')
    
    args = { 'length': VariableRef(Variable(value=2, constant=True)) }
    stmt = Merge([Function.call(VariableRef(gen), args)])
    
    limit = VariableRef(Variable(value=6, constant=True))
    stmt = Store(stmt, [GroupRef(grp, limit)])
    
    context = { 'int_counter': int_counter, 'population': [] }
    
    stmt.execute(context)

    actual = context['population']
    expected = [[0, 0], [1, 1], [2, 2], [3, 3], [4, 4], [5, 5]]
    assert expected == actual, "Expected: %s; Actual: %s" % (expected, actual)

def test_filter():
    def if_over_n(_source, n):
        for i in _source:
            if i > n: yield i

    context = {
        'if_over_n': if_over_n,
        'pop': [1, 2, 3, 4, 5, 6, 7, 8, 7, 6, 5, 4, 3, 2, 1],
        'dest': []
    }

    stmt = Merge([GroupRef(Variable('pop'))])
    stmt = Operator(stmt, Function.call(VariableRef(Variable('if_over_n', external=True)), { 'n': VariableRef(Variable(value=5, constant=True)) }))
    stmt = Store(stmt, [GroupRef(Variable('dest'))])

    stmt.execute(context)

    actual = context['dest']
    expected = [6, 7, 8, 7, 6]
    assert expected == actual, "Expected: %s; Actual: %s" % (expected, actual)

