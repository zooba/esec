from nose.tools import raises, assert_raises
import esdlc.errors as error
from esdlc.lexer import _tokenise
from esdlc.nodes import *

def test_node_bases():
    assert issubclass(UnknownNode, NodeBase)
    assert issubclass(FunctionNode, NodeBase)
    assert issubclass(NameNode, NodeBase)
    assert issubclass(TextNode, NodeBase)
    assert issubclass(ValueNode, NodeBase)
    assert issubclass(VariableNode, NodeBase)
    assert issubclass(BacktickNode, NodeBase)
    assert issubclass(GroupNode, NodeBase)
    assert issubclass(FromSourceNode, NodeBase)
    assert issubclass(FromNode, NodeBase)
    assert issubclass(JoinSourceNode, NodeBase)
    assert issubclass(JoinNode, NodeBase)
    assert issubclass(EvalNode, NodeBase)
    assert issubclass(YieldNode, NodeBase)
    assert issubclass(BlockNode, NodeBase)
    assert issubclass(RepeatNode, NodeBase)
    
    assert issubclass(VariableNode, NameNode)
    assert issubclass(BacktickNode, TextNode)
    assert issubclass(BlockNode, NameNode)
    assert issubclass(RepeatNode, BlockNode)

def check_Node_parse(source, node_type, expected):
    tokens = list(_tokenise(source))
    count, node = node_type.parse(tokens, 0)
    
    print repr(node)
    assert isinstance(node, node_type)
    print repr(expected)
    assert repr(expected) == repr(node)

def check_Node_parse_fail(source, node_type, expect):
    def _test(src):
        tokens = list(_tokenise(src))
        print tokens
        count, node = node_type.parse(tokens, 0)
        print repr(node)
    assert_raises(callableObj=_test, excClass=expect, src=source)

def test_ValueNode_parse():
    for source, expect in [
        ("TRUE", True),
        ("FALSE", False),
        ("NULL", None), ("NONE", None),
        ("1", 1.0), ("2", 2.0), ("100", 100.0), ("1000000", 1000000.0),
        ("1.", 1.0), ("1.0", 1.0), ("1.1", 1.1), ("1.01", 1.01),
        (".1", 0.1), ("0.1", 0.1), (".0001", 0.0001), ("0.0001", 0.0001),
        ("1e1", 10.0), ("1.e1", 10.0), ("1.0e1", 10.0), ("1.0e+1", 10.0),
        ("1e-1", 0.1), ("1.e-1", 0.1), ("1.0e-1", 0.1), 
        ]:
        yield check_Node_parse, source, ValueNode, ValueNode(expect, None)

    for source, expect in [
        ("", error.InvalidSyntaxError),     # tokenises as eos
        (" ", error.InvalidSyntaxError),    # tokenises as eos
        ("-1", error.InvalidSyntaxError),   # - is an operator
        ("name", error.InvalidSyntaxError), # name is a name
        ("+2", error.InvalidSyntaxError),   # + is an operator
        ("0e+-4", error.InvalidNumberError),# 0e+ cannot be converted to a number
        ]:
        yield check_Node_parse_fail, source, ValueNode, expect

def test_VariableNode_parse():
    for source, expect in [
        ("undottedname", "undottedname"),
        ("dotted.name", "dotted"),
        ("underscore_name", "underscore_name"),
        ("indexed[name]", "indexed"),   # [ operator is not handled by VariableNode
        ("_leading_underscore", "_leading_underscore"),
        ("embedded123numbers", "embedded123numbers"),
        ("MixedCaseName", "mixedcasename"),
        ]:
        yield check_Node_parse, source, VariableNode, VariableNode(expect, None)
    
    for source in [
        "", " ",                # tokens == [eos]
        "1", ".1", "0.2",       # tokens == [number]
        "-1", ".name", "+8",    # tokens == [operator]
        # reserved words
        "from", "select", "using", "join", "into", "repeat", "begin", "end", "yield", "eval",
        ]:
        yield check_Node_parse_fail, source, VariableNode, error.InvalidSyntaxError

def test_BacktickNode_parse():
    for source, expect in [
        ("`with backtick", "with backtick")
        ]:
        yield check_Node_parse, source, BacktickNode, BacktickNode(expect, None)
    
    for source, expect in [
        ("without backtick", error.InvalidSyntaxError)
        ]:
        yield check_Node_parse_fail, source, BacktickNode, expect

def test_GroupNode_parse():
    def _v(n): return VariableNode(n, None)
    def _f(n, **kw): return FunctionNode(n, None, **kw)
    def _p(s): return UnknownNode.parse(list(_tokenise(s)), 0)[1]
    
    for source, expect_group, expect_size in [
        ("population", _v("population"), None),
        ("MixedCasePopulation", _v("mixedcasepopulation"), None),
        ("generator()", _f("generator"), None),
        ("generator(arg=value)", _f("generator", arg=_p("value")), None),
        ("1 population", _v("population"), _p("1.0")),
        ("1 generator()", _f("generator"), _p("1.0")),
        ("1 generator(arg=value)", _f("generator", arg=_p("value")), _p("1.0")),
        ("(1+1) population", _v("population"), _p("1+1")),
        ("(1+1) generator()", _f("generator"), _p("1+1")),
        ("(1+1) generator(arg=value)", _f("generator", arg=_p("value")), _p("1+1")),
        ("1 + 1 population", _v("population"), _p("1+1")),
        ("1 + 1 generator()", _f("generator"), _p("1+1")),
        ("1 + 1 generator(arg=value)", _f("generator", arg=_p("value")), _p("1+1")),
        ("var 1", _v("var"), None),
        # using a _list for size is caught by Verifier
        ("[1,2] v", _v("v"), _f("_list", **{"#0": _p("1"), "#1": _p("2")})),
        ]:
        yield check_Node_parse, source, GroupNode, GroupNode(expect_group, expect_size, None)
    
    for source, expect in [
        ("1 1", error.ExpectedGroupError),
        ("-1", error.ExpectedGroupError),   # _uop_- is not a generator
        ("1+1", error.ExpectedGroupError),  # _op_+ is not a generator
        ("v=1", error.ExpectedGroupError),  # _assign is not a generator
        ("var (group)", error.ExpectedParameterValueError),  # var (group) is a bad function call
        ]:
        yield check_Node_parse_fail, source, GroupNode, expect

def test_FromNode_parse():
    def _g(s): return GroupNode.parse(list(_tokenise(s)), 0)[1]
    def _v(n): return VariableNode(n, None)
    def _f(n, *p, **kw): return FunctionNode(n, None, *p, **kw)
    def _fs(g): return FromSourceNode(g, None)
    def _p(s): return UnknownNode.parse(list(_tokenise(s)), 0)[1]
    
    for source, srcs, dests, usings in [
        ("FROM population SELECT offspring", [_g("population")], [_g("offspring")], None),
        ("FROM population SELECT 2 offspring", [_g("population")], [_g("2 offspring")], None),
        ("FROM pA, pB, pC SELECT oA, oB, oC", [_g("pA"), _g("pB"), _g("pC")], [_g("oA"), _g("oB"), _g("oC")], None),
        ("FROM pA, pB, pC SELECT 1 oA, 2 oB, 3 oC", [_g("pA"), _g("pB"), _g("pC")], [_g("1 oA"), _g("2 oB"), _g("3 oC")], None),
        # sizes on source groups are caught by Verifier
        ("FROM 1 pA, 2 pB, 3 pC SELECT oA, oB, oC", [_g("1 pA"), _g("2 pB"), _g("3 pC")], [_g("oA"), _g("oB"), _g("oC")], None),
        
        ("FROM p SELECT o USING filter", [_g("p")], [_g("o")], _f('filter')),
        ("FROM p SELECT o USING fA, fB", [_g("p")], [_g("o")], _f('fB', _source=_f('fA'))),
        ("FROM p SELECT o USING filter(param=value)", [_g("p")], [_g("o")], _f('filter', param=_v("value"))),
        ]:
        if usings is None:
            usings = _fs(srcs)
        else:
            u = usings
            while '_source' in u.arguments: u = u.arguments['_source']
            u.arguments['_source'] = _fs(srcs)
        yield check_Node_parse, source, FromNode, FromNode(srcs, dests, usings, None)
    
    for source, expect in [
        ("FROM populaton USING repeated", error.ExpectedSelectError),
        ("FROM var var populaton SELECT offspring", error.ExpectedSelectError),
        ("SELECT var FROM population USING repeated", error.InvalidSyntaxError),
        ("FROM p SELECT o USING fA fB", error.ExpectedCommaError),
        ("FROM SELECT o USING fA fB", error.ExpectedGroupError),
        ("FROM p SELECT USING fA fB", error.ExpectedGroupError),
        ("FROM p SELECT o USING", error.ExpectedFilterError),
        ("FROM 1 pA() SELECT 2 oA()", error.GeneratorAsDestinationError),
        ]:
        yield check_Node_parse_fail, source, FromNode, expect

def test_JoinNode_parse():
    def _g(s): return GroupNode.parse(list(_tokenise(s)), 0)[1]
    def _v(n): return VariableNode(n, None)
    def _f(n, *p, **kw): return FunctionNode(n, None, *p, **kw)
    def _p(s): return UnknownNode.parse(list(_tokenise(s)), 0)[1]
    
    for source, srcs, dests, usings in [
        ("JOIN population INTO offspring", [_g("population")], [_g("offspring")], None),
        ("JOIN population INTO 2 offspring", [_g("population")], [_g("2 offspring")], None),
        ("JOIN pA, pB, pC INTO oA, oB, oC", [_g("pA"), _g("pB"), _g("pC")], [_g("oA"), _g("oB"), _g("oC")], None),
        ("JOIN pA, pB, pC INTO 1 oA, 2 oB, 3 oC", [_g("pA"), _g("pB"), _g("pC")], [_g("1 oA"), _g("2 oB"), _g("3 oC")], None),
        # sizes on source groups are caught by Verifier
        ("JOIN 1 pA, 2 pB, 3 pC INTO oA, oB, oC", [_g("1 pA"), _g("2 pB"), _g("3 pC")], [_g("oA"), _g("oB"), _g("oC")], None),
        
        ("JOIN p INTO o USING filter", [_g("p")], [_g("o")], _f('filter')),
        ("JOIN p INTO o USING fA, fB", [_g("p")], [_g("o")], _f('fB', _source=_f('fA'))),
        ("JOIN p INTO o USING filter(param=value)", [_g("p")], [_g("o")], _f('filter', param=_v("value"))),
        ]:
        if usings is None:
            usings = JoinSourceNode(srcs, None)
        else:
            u = usings
            while '_source' in u.arguments: u = u.arguments['_source']
            u.arguments['_source'] = JoinSourceNode(srcs, None)
        yield check_Node_parse, source, JoinNode, JoinNode(srcs, dests, usings, None)
    
    for source, expect in [
        ("JOIN populaton USING repeated", error.ExpectedIntoError),
        ("JOIN var var populaton INTO offspring", error.ExpectedIntoError),
        ("INTO var JOIN population USING repeated", error.InvalidSyntaxError),
        ("JOIN p INTO o USING fA fB", error.ExpectedCommaError),
        ("JOIN INTO o USING fA fB", error.ExpectedGroupError),
        ("JOIN p INTO USING fA fB", error.ExpectedGroupError),
        ("JOIN p INTO o USING", error.ExpectedFilterError),
        ("JOIN 1 pA() INTO 2 oA()", error.GeneratorAsDestinationError),
        ]:
        yield check_Node_parse_fail, source, JoinNode, expect

def test_EvalNode_parse():
    def _g(s): return GroupNode.parse(list(_tokenise(s)), 0)[1]
    def _v(n): return VariableNode(n, None)
    def _f(n, *p, **kw): return FunctionNode(n, None, *p, **kw)
    def _p(s): return UnknownNode.parse(list(_tokenise(s)), 0)[1]
    
    for source, srcs, usings in [
        ("EVAL population", [_g("population")], None),
        # size specifiers are caught by Verifier
        ("EVAL 5 population", [_g("5 population")], None),
        ("EVALUATE population", [_g("population")], None),
        ("EVAL population USING func()", [_g("population")], [_f("func")]),
        ("EVAL population USING fA(), fB", [_g("population")], [_f("fA"), _v("fB")]),
        ]:
        yield check_Node_parse, source, EvalNode, EvalNode(srcs, usings, None)
    
    for source, expect in [
        ("EVAL USING func", error.ExpectedGroupError),
        ("EVAL pop USING", error.ExpectedEvaluatorError),
        ("EVAL p USING fA fB", error.ExpectedCommaError),
        ("USING fA EVAL p", error.InvalidSyntaxError),
        ]:
        yield check_Node_parse_fail, source, EvalNode, expect

def test_YieldNode_parse():
    def _g(s): return GroupNode.parse(list(_tokenise(s)), 0)[1]
    def _v(n): return VariableNode(n, None)
    def _f(n, *p, **kw): return FunctionNode(n, None, *p, **kw)
    def _p(s): return UnknownNode.parse(list(_tokenise(s)), 0)[1]
    
    for source, srcs in [
        ("YIELD population", [_g("population")]),
        ("YIELD pA, pB", [_g("pA"), _g("pB")]),
        # size specifiers are caught by Verifier
        ("YIELD 5 population", [_g("5 population")]),
        ("YIELD pA pB", [_g("pA pB")]),
        ]:
        yield check_Node_parse, source, YieldNode, YieldNode(srcs, None)
    
    for source, expect in [
        ("YIELD", error.ExpectedGroupError),
        ("YIELD pA pB pC", error.ExpectedCommaError),
        ]:
        yield check_Node_parse_fail, source, YieldNode, expect
