from esdlc.ast import parse
from esdlc.model import AstSystem

def check(input, output=None):
    ast = parse(input)
    if ast.errors or ast.warnings:
        print ast.format()
        print 'Errors:\n  ' + '\n  '.join(str(i) for i in ast.errors)
        print 'Warnings:\n  ' + '\n  '.join(str(i) for i in ast.warnings)
        assert False
    model = AstSystem(ast)
    validation = model.validate()
    if not validation:
        print ast.format()
        print 'Errors:\n  ' + '\n  '.join(str(i) for i in validation.errors)
        print 'Warnings:\n  ' + '\n  '.join(str(i) for i in validation.warnings)
        assert validation
    
    code = model.as_esdl().strip()
    assert code == (output or input), "Expected %s\nActual %s" % (output or input, code)

def test_arithmetic():
    yield check, "i=1+2*3-4/5^2", "i = ((1.0+(2.0*3.0))-(4.0/(5.0^2.0)))"
    yield check, "i=(1+2*3-4)/5^2", "i = (((1.0+(2.0*3.0))-4.0)/(5.0^2.0))"
    yield check, "i=1+2*(3-4)/5^2", "i = (1.0+((2.0*(3.0-4.0))/(5.0^2.0)))"

    yield check, "i=A+B*C-D/E^B", "i = ((a+(b*c))-(d/(e^b)))"
    yield check, "i=(A+B*C-D)/E^B", "i = (((a+(b*c))-d)/(e^b))"
    yield check, "i=A+B*(C-D)/E^B", "i = (a+((b*(c-d))/(e^b)))"

def test_functions():
    yield check, "i=A(x)+B(y)+C(z)", "i = ((a(x)+b(y))+c(z))"
    yield check, "i=A(x=1)+B(y=2+3)+C(z=4*A)", "i = ((a(x=1.0)+b(y=(2.0+3.0)))+c(z=(4.0*a)))"

def test_members():
    for p1 in ['()', '[i]']:
        p2 = (p1, p1)
        p3 = (p1, p1, p1)
        yield check, "i = A.B.C", "i = a.b.c"
        yield check, "i = A.B.C%s" % p1, "i = a.b.c%s" % p1
        yield check, "i = A.B%s.C" % p1, "i = a.b%s.c" % p1
        yield check, "i = A%s.B.C" % p1, "i = a%s.b.c" % p1
        yield check, "i = A.B%s.C%s" % p2, "i = a.b%s.c%s" % p2
        yield check, "i = A%s.B.C%s" % p2, "i = a%s.b.c%s" % p2
        yield check, "i = A%s.B%s.C" % p2, "i = a%s.b%s.c" % p2
        yield check, "i = A%s.B%s.C%s" % p3, "i = a%s.b%s.c%s" % p3

def test_fromstmt():
    yield check, "FROM source SELECT destination", None
    yield check, "FROM source1, source2 SELECT destination", None
    yield check, "FROM source SELECT (100.0) destination1, destination2", None
    yield check, "FROM source SELECT (100.0) destination1, (size) destination2", None
    yield check, "FROM source1, source2 SELECT (100.0) destination1, (size) destination2", None
    yield check, "FROM source(length=10.0) SELECT destination", None
    
    yield check, "FROM source SELECT destination USING operator()", None
    yield check, "FROM source SELECT destination USING operator", "FROM source SELECT destination USING operator()"
    yield check, "FROM source SELECT destination USING operator(rate=1.0)", None
    yield check, "FROM source SELECT destination USING operator(rate=(1.0/size))", None

