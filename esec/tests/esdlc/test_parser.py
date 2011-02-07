from esdlc.parser import AST
from esdlc.lexer import tokenise
from esdlc.nodes import *

def get_tokens(source):
    tokens = []
    for stmt in tokenise(source): tokens.extend(stmt)
    return tokens

def test_arithmetic():
    source = 'x = (-b + sqrt(value=b^2 - (4 * a) * c)) / (2 * a)'
    tokens = get_tokens(source)
    count, node = UnknownNode.parse(tokens, 0)
    
    print count, len(tokens) - 1
    assert count == len(tokens) - 1 # ignore eos
    
    print repr(node)
    assert isinstance(node, FunctionNode)
    assert node.name == '_assign'
    
    dest = node.arguments['destination']
    print repr(dest)
    assert isinstance(dest, VariableNode)
    assert dest.name == 'x'
    
    src = node.arguments['source']
    print repr(src)
    assert isinstance(src, FunctionNode)
    assert src.name == '_op_/'
    
    right = src.arguments['#1']
    print repr(right)
    assert isinstance(right, FunctionNode)
    assert right.name == '_op_*'
    
    left, right = right.arguments['#0'], right.arguments['#1']
    print repr(left), '*', repr(right)
    assert isinstance(left, ValueNode)
    assert left.value == 2.0
    assert isinstance(right, VariableNode)
    assert right.name == 'a'
    
    left = src.arguments['#0']
    print repr(left)
    assert isinstance(left, FunctionNode)
    assert left.name == '_op_+'
    
    left, right = left.arguments['#0'], left.arguments['#1']
    print repr(left), repr(right)
    assert isinstance(left, FunctionNode)
    assert left.name == '_uop_-'
    
    print repr(left.arguments['#0'])
    assert isinstance(left.arguments['#0'], VariableNode)
    assert left.arguments['#0'].name == 'b'
    
    print repr(right)
    assert isinstance(right, FunctionNode)
    assert right.name == 'sqrt'
    
    value = right.arguments['value']
    print repr(value)
    assert isinstance(value, FunctionNode)
    assert value.name == '_op_-'
    
    left, right = value.arguments['#0'], value.arguments['#1']
    print repr(left), '-', repr(right)
    assert isinstance(left, FunctionNode)
    assert left.name == '_op_^'
    
    print repr(left.arguments['#0']), '^', repr(left.arguments['#1'])
    assert isinstance(left.arguments['#0'], VariableNode)
    assert left.arguments['#0'].name == 'b'
    assert isinstance(left.arguments['#1'], ValueNode)
    assert left.arguments['#1'].value == 2.0
    
    assert isinstance(right, FunctionNode)
    assert right.name == '_op_*'
    
    print repr(right.arguments['#0']), '*', repr(right.arguments['#1'])
    assert isinstance(right.arguments['#1'], VariableNode)
    assert right.arguments['#1'].name == 'c'
    left = right.arguments['#0']
    
    assert isinstance(left, FunctionNode)
    assert left.name == '_op_*'
    assert isinstance(left.arguments['#0'], ValueNode)
    assert left.arguments['#0'].value == 4.0
    assert isinstance(left.arguments['#1'], VariableNode)
    assert left.arguments['#1'].name == 'a'
    
def test_function_calls():
    source = 'assign_dest = func_name(arg_name_1=value,arg_name_2=1)'
    tokens = get_tokens(source)
    count1, node1 = UnknownNode.parse(tokens, 0)
    count2, node2 = FunctionNode.parse(tokens, 2)
    
    print count1, len(tokens) - 1
    assert count1 == len(tokens) - 1 # ignore eos
    print count2, len(tokens) - 1
    assert count2 == len(tokens) - 1 # ignore eos
    
    assert count1 == count2
    
    node = node1
    
    print repr(node)
    assert isinstance(node, FunctionNode)
    assert node.name == '_assign'
    
    dest = node.arguments['destination']
    print repr(dest)
    assert isinstance(dest, VariableNode)
    assert dest.name == 'assign_dest'
    
    src = node.arguments['source']
    print repr(src)
    assert isinstance(src, FunctionNode)
    assert src.name == 'func_name'
    assert src.name == node2.name
    
    print repr(node2)
    assert repr(src) == repr(node2)
    
    print src.arguments
    assert len(src.arguments) == 2
    assert 'arg_name_1' in src.arguments
    assert 'arg_name_2' in src.arguments
    
    arg1, arg2 = src.arguments['arg_name_1'], src.arguments['arg_name_2']
    
    print repr(arg1)
    assert isinstance(arg1, VariableNode)
    assert arg1.name == 'value'
    
    print repr(arg2)
    assert isinstance(arg2, ValueNode)
    assert arg2.value == 1.0
    
