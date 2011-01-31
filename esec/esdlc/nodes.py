'''A set of nodes that make up an ESDL AST.
'''
# Disable: Too few public methods
#          Too many lines in module
#pylint: disable=R0903,C0302

from __future__ import absolute_import
from esdlc.lexer import Token
import esdlc.errors as error

def _get_token(tokens, token_i):
    '''Returns the token at index `token_i` of `tokens` if `token_i` is
    a valid index and the token at that index is not an end-of-statement
    marker. Otherwise, returns ``None``.
    '''
    if token_i < len(tokens):
        token = tokens[token_i]
        if token and token.tag == 'eos':
            token = None
        return token
    else:
        return None

class NodeBase(object):
    '''The base class of all AST nodes.'''
    
    tag = ''
    '''Identifies the type of the node without requiring RTTI checks.'''
    
    def __init__(self, tokens=None):
        '''Initialises a node.
        
        :Warn: This method should only be called by derived classes.
        '''
        
        assert type(self) is not NodeBase, "Do not instantiate NodeBase directly."
        self.tokens = tokens or []
        '''Contains the lexer tokens used to parse this node.'''
        
        if self.tokens: self.tokens = sorted(self.tokens)

class UnknownNode(NodeBase):
    '''Represents an unidentified node. This normally indicates an error
    in the ESDL source.
    
    The `parse` method of this class is used to begin parsing
    unidentified tokens.'''
    tag = 'unknown'
    
    def __init__(self, text, tokens):
        '''Initialises an `UnknownNode` with text.'''
        super(UnknownNode, self).__init__(tokens)
        self.text = text or ''
    
    def __str__(self): return '<?> ' + str(self.text) + ' <?>'
    
    @classmethod
    def parse(cls, tokens, first_token):
        '''Parses an unidentified sequence of tokens.
        
        `tokens` is a list of tokens, `first_token` is the index of the
        token to start parsing at.
        
        Returns ``(next_token, NodeBase)``, where ``next_token`` is the
        index of the token following the parsed sequence.
        
        :Note: 
            ``BEGIN``, ``REPEAT`` and ``END`` commands are not parsed by
            this method.'''
        assert tokens, "tokens must be provided"
        if not 0 <= first_token < len(tokens): return first_token, None
        
        first = _get_token(tokens, first_token)
        if not first:
            return first_token + 1, None
        elif first.tag in ('BEGIN', 'REPEAT', 'END'):
            raise error.UnexpectedStatementError(tokens[first_token], first.tag)
        elif first.tag == 'FROM':
            return FromNode.parse(tokens, first_token)
        elif first.tag == 'JOIN':
            return JoinNode.parse(tokens, first_token)
        elif first.tag == 'YIELD':
            return YieldNode.parse(tokens, first_token)
        elif first.tag == 'EVAL':
            return EvalNode.parse(tokens, first_token)
        elif first.tag == '`':
            return BacktickNode.parse(tokens, first_token)
        
        # Assume to be mathematical expression, possibly including
        # function calls
        token_i = first_token
        stack = []
        expect = 'operand'
        token = _get_token(tokens, token_i)
        
        while token and expect in ('operand', 'operator'):
            if expect == 'operand':
                token_i, expect = cls._read_operand(tokens, token_i, stack)
            elif expect == 'operator':
                token_i, expect = cls._read_operator(tokens, token_i, stack)
            
            token = _get_token(tokens, token_i)
        
        cls._reduce_stack_attributes(stack)
        for op in '~': cls._reduce_stack_unary_ops(stack, op)
        for op in '^': cls._reduce_stack_binary_ops(stack, op, left_to_right=False)
        for op in '%/*-+=': cls._reduce_stack_binary_ops(stack, op, left_to_right=True)
        
        if len(stack) == 1:
            return token_i, stack[0]
        elif len(stack) > 1 or not token:
            raise error.InvalidSyntaxError(tokens[first_token])
        else:
            return token_i, UnknownNode(token.value, [token])
    
    
    @classmethod
    def _read_operand(cls, tokens, token_i, stack):
        '''Reads an operand from `tokens`. Returns a tuple containing an
        updated value of `token_i` and one of ``'operand'``,
        ``'operator'`` or ``None`` specifying what is expected next.
        '''
        token = _get_token(tokens, token_i)
        expect = 'operand'
        
        if token.tag in ('number', 'constant'):
            token_i, value = ValueNode.parse(tokens, token_i)
            stack.append(value)
            expect = 'operator'
        elif token.tag == 'name':
            token1 = _get_token(tokens, token_i + 1)
            
            if stack and stack[-1].tag == '.':
                stack.pop()
                stack.pop()
                base = stack.pop()
                value = TextNode(token.value, [token])
                base = FunctionNode('_getattr', base.tokens + value.tokens, source=base, attr=value)
                if token1 and token1.tag == '(':
                    token_i, value = FunctionNode.parse_arguments('_call', tokens, token_i + 1, _target=base)
                else:
                    token_i += 1
                    value = base
            else:
                if token1 and token1.tag == '(':
                    token_i, value = FunctionNode.parse(tokens, token_i)
                else:
                    token_i, value = VariableNode.parse(tokens, token_i)
            stack.append(value)
            expect = 'operator'
        elif token.tag == '-':  #unary operator
            stack.append('~')
            stack.append(token)
            token_i += 1
        elif token.tag == '(':  #recurse into parentheses
            old_token_i = token_i
            token_i, value = UnknownNode.parse(tokens, token_i + 1)
            if value: stack.append(value)
            token = _get_token(tokens, token_i)
            if token and token.tag == ')':
                token_i += 1
            else:
                if value: stack.pop()
                token_i, func = FunctionNode.parse_list(tokens, old_token_i)
                stack.append(func)
            expect = 'operator' if value else 'operand'
        elif token.tag == '[':  #read list
            token_i, func = FunctionNode.parse_list(tokens, token_i)
            stack.append(func)
            expect = 'operator'
        else:
            expect = None
        
        return token_i, expect
    
    @classmethod
    def _read_operator(cls, tokens, token_i, stack):
        '''Reads an operator from `tokens`. Returns a tuple containing
        an updated value of `token_i` and one of ``'operand'``,
        ``'operator'`` or ``None`` specifying what is expected next.
        '''
        token = _get_token(tokens, token_i)
        
        if token.tag in ('name', 'number'):
            expect = None
        elif len(token.tag) == 1 and token.tag in '^%/*-+=.':
            stack.append(token.tag)
            stack.append(token)
            expect = 'operand'
            token_i += 1
        elif token.tag == '(':  #read function
            token_i, func = FunctionNode.parse_arguments('_call', tokens, token_i, _target=stack.pop())
            stack.append(func)
            expect = 'operator'
        elif token.tag == '[':  #read subscript
            token1 = _get_token(tokens, token_i + 1)
            if not token1 or token1.tag == ']': raise error.ExpectedIndexError(token)
            token_i, key = UnknownNode.parse(tokens, token_i + 1)
            if not key: raise error.ExpectedIndexError(token)
            source = stack.pop()
            stack.append(FunctionNode('_getitem', source.tokens, source=source, key=key))
            token_i += 1
            expect = 'operator'
        else:
            expect = None
        
        return token_i, expect
    
    @classmethod
    def _reduce_stack_attributes(cls, stack):
        '''Merges attribute specifies in `stack` into `FunctionNode`s
        calling ``_getattr``.
        '''
        op = '.'
        while op in stack:
            i = stack.index(op)
            if not 0 < i < len(stack) - 2: raise error.InvalidSyntaxError(stack[i+1])
            val1, _, op_token, val2 = stack[i-1:i+3]
            if 1 < i and isinstance(stack[i-2], str): raise error.InvalidSyntaxError(op_token)
            if isinstance(val2, str): raise error.InvalidSyntaxError(stack[i+3])
            op_tokens = val1.tokens + val2.tokens
            op_tokens.append(op_token)
            if val2.tag == 'variable':
                name = TextNode(val2.name, val2.tokens)
                stack[i-1:i+3] = [FunctionNode('_getattr', op_tokens, source=val1, attr=name)]
            else:
                stack[i-1:i+3] = [FunctionNode('_getattr', op_tokens, source=val1, attr=val2)]
    
    @classmethod
    def _reduce_stack_unary_ops(cls, stack, op):
        '''Reduces unary operators into `FunctionNode`s where the name
        of the function begins with ``_uop_``.
        '''
        while op in stack:
            i = stack.index(op)
            if not i < len(stack)-2: raise error.InvalidSyntaxError(stack[i+1])
            op_token, val = stack[i+1:i+3]
            if isinstance(val, str): raise error.InvalidSyntaxError(stack[i+3])
            op_tokens = list(val.tokens)
            op_tokens.append(op_token)
            stack[i:i+3] = [FunctionNode('_uop_' + op_token.tag, op_tokens, val)]
    
    @classmethod
    def _reduce_stack_binary_ops(cls, stack, op, left_to_right=True):
        '''Reduces binary operators into `FunctionNode`s where the name
        of the function begins with ``_op_``. Assignment operators are
        also reduced and use the function ``_assign``.
        '''
        if left_to_right:
            while op in stack:
                i = stack.index(op)
                if not 0 < i < len(stack) - 2: raise error.InvalidSyntaxError(stack[i+1])
                val1, _, op_token, val2 = stack[i-1:i+3]
                if i >= 2 and isinstance(stack[i-2], str): raise error.InvalidSyntaxError(op_token)
                if isinstance(val2, str): raise error.InvalidSyntaxError(stack[i+3])
                op_tokens = val1.tokens + val2.tokens
                op_tokens.append(op_token)
                if op == '=':
                    stack[i-1:i+3] = [FunctionNode('_assign', op_tokens, destination=val1, source=val2)]
                else:
                    stack[i-1:i+3] = [FunctionNode('_op_' + op_token.tag, op_tokens, *(val1, val2))]
        
        else:
            stack.reverse()
            while op in stack:
                i = stack.index(op)
                if not 2 <= i < len(stack): raise error.InvalidSyntaxError(stack[i-1])
                val1, _, op_token, val2 = reversed(stack[i-2:i+2])
                if i < len(stack) - 1 and isinstance(stack[i+1], str): raise error.InvalidSyntaxError(op_token)
                if isinstance(val2, str): raise error.InvalidSyntaxError(stack[i-3])
                op_tokens = val1.tokens + val2.tokens
                op_tokens.append(op_token)
                stack[i-2:i+2] = [FunctionNode('_op_' + op_token.tag, op_tokens, *(val1, val2))]
            stack.reverse()


class FunctionNode(NodeBase):
    '''Represents a function call.'''
    tag = 'function'
    
    def __init__(self, name, tokens, *positional_arguments, **named_arguments):
        super(FunctionNode, self).__init__(tokens)
        
        if isinstance(name, NodeBase):
            if name.tag in ('name', 'variable'):
                name = name.name
            elif name.tag == 'function':
                named_arguments['_target'] = name
                name = '_call'
        
        assert isinstance(name, str), "name must be a string (" + repr(name) + ")"
        self.name = name.lower()
        
        self.arguments = dict((key.lower(), value) for key, value in named_arguments.iteritems())
        for i, value in enumerate(positional_arguments):
            self.arguments['#%d' % i] = value
    
    def __str__(self):
        if self.name == '_assign':
            return '%(destination)s = %(source)s' % self.arguments
        elif self.name == '_getattr':
            if self.arguments['attr'].tag == 'text':
                return '%s.%s' % (self.arguments['source'], self.arguments['attr'].text)
            else:
                return 'getattr(%(source)s, %(attr)s)' % self.arguments
        elif self.name == '_getitem':
            return '%(source)s[%(key)s]' % self.arguments
        elif self.name == '_call':
            args = sorted((i for i in self.arguments.iteritems() if i[0] != '_target'), key=lambda i: i[0])
            arglist = (['%s' % item[1] for item in args if item[0][0] == '#'] +
                       ['%s=%s' % item for item in args if item[0][0] != '#'])
            arg_string = ','.join(arglist)
            return str(self.arguments['_target']) + '(' + arg_string + ')'
        elif self.name == '_list':
            arglist = [value for key, value in sorted(self.arguments.iteritems(), key=lambda i: i[0]) if key[0] == '#']
            return '[%s]' % ', '.join(str(arg) for arg in arglist)
        elif self.name.startswith('_op_'):
            return '(%s %s %s)' % (self.arguments['#0'], self.name[4:], self.arguments['#1'])
        elif self.name.startswith('_uop_'):
            return '(%s%s)' % (self.name[5:], self.arguments['#0'])
        elif self.arguments:
            args = sorted(self.arguments.iteritems(), key=lambda i: i[0])
            arglist = (['%s' % item[1] for item in args if item[0][0] == '#'] +
                       ['%s=%s' % item for item in args if item[0][0] != '#'])
            arg_string = ','.join(arglist)
        else:
            arg_string = ''
        return self.name + '(' + arg_string + ')'
    
    def __repr__(self): return self.tag + ':' + str(self)
    
    @classmethod
    def parse(cls, tokens, first_token, **other_args):
        '''Reads a `FunctionNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        
        token_i, func = cls.parse_maybe_variable(tokens, first_token, **other_args)
        if func.tag == 'variable':
            func = FunctionNode(func.name, tokens[first_token:token_i])
        
        return token_i, func
    
    @classmethod
    def parse_maybe_variable(cls, tokens, first_token, **other_args):
        '''Reads a `FunctionNode` from `tokens`. If it looks like a
        variable (or object reference), a `VariableNode` is returned
        instead.
        '''
        assert tokens, "tokens must be provided"
        token_i = first_token
        
        func_name_tokens = []
        token = _get_token(tokens, token_i)
        if not token: raise error.InvalidFunctionCallError(tokens[-1])
        while token:
            if token and token.tag in ('name', '['):
                func_name_tokens.append(token)
                token_i += 1
                token = _get_token(tokens, token_i)
            else:
                break
            
            if token and token.tag in ('.'):
                func_name_tokens.append(token)
                token_i += 1
                token = _get_token(tokens, token_i)
            else:
                break
        
        if not func_name_tokens: raise error.InvalidFunctionCallError(tokens[first_token])
        _, func_name = UnknownNode.parse(func_name_tokens, 0)
        token = _get_token(tokens, token_i)
        
        if token and token.tag == '(':
            token_i, func = cls.parse_arguments(func_name, tokens, token_i, **other_args)
            func.tokens = sorted(tokens[first_token:token_i])
        elif other_args:
            func = FunctionNode(func_name, tokens[first_token:token_i], **other_args)
        elif func_name.tag == 'name':
            func = VariableNode(str(func_name), tokens[first_token:token_i])
        else:
            func = func_name
        return token_i, func
        
    @classmethod
    def parse_arguments(cls, func_name, tokens, first_token, **other_args):
        '''Reads arguments for the given function.
        
        ``tokens[first_token]`` must be the opening parenthesis,
        otherwise this method assumes that the function has no
        parameters.
        '''
        assert tokens, "tokens must be provided"
        token_i = first_token
        token = _get_token(tokens, token_i)
        func_args = {}
        
        if not token or token.tag != '(':
            return token_i, FunctionNode(func_name, tokens[first_token:token_i], **other_args)
        
        token_i += 1
        token = _get_token(tokens, token_i)
        
        while token and token.tag != ')':
            if token.tag != 'name': raise error.InvalidParameterNameError(token)
            arg_name = token.value
            
            token_i += 1
            token = _get_token(tokens, token_i)
            
            if not token: raise error.ExpectedParameterValueError(tokens[-1])
            if token.tag == 'eos': raise error.ExpectedParameterValueError(token)
            
            if token.tag == '=':
                token_i += 1
                token_i, arg_node = UnknownNode.parse(tokens, token_i)
                func_args[arg_name] = arg_node
            else:
                func_args[arg_name] = VariableNode(arg_name, [tokens[token_i-1]])
                func_args[arg_name].implicit = True
            
            token = _get_token(tokens, token_i)
            if token and token.tag == ',': token_i += 1
            token = _get_token(tokens, token_i)
        
        if not token: raise error.UnmatchedBracketError(tokens[-1], ')')
        
        token_i += 1
        func_args.update(other_args)
        return token_i, FunctionNode(func_name, tokens[first_token:token_i], **func_args)
    
    @classmethod
    def parse_list(cls, tokens, first_token):
        '''Reads a `FunctionNode` with name ``'_list'`` from `tokens`.
        
        ``tokens[first_token]`` should be the opening parenthesis or
        bracket.
        '''
        assert tokens, "tokens must be provided"
        token_i = first_token
        func_args = []
        
        token = _get_token(tokens, token_i)
        if not token: raise error.InvalidFunctionCallError(tokens[-1])
        if token.tag not in ('[', '('): raise error.InvalidFunctionCallError(token)
        expect = { '[': ']', '(': ')'}[token.tag]
        func_name = '_list'
        
        token_i += 1
        token = _get_token(tokens, token_i)
        
        while token and token.tag != expect:
            token_i, arg_node = UnknownNode.parse(tokens, token_i)
            func_args.append(arg_node)
            
            token = _get_token(tokens, token_i)
            if token and token.tag == ',': token_i += 1
            token = _get_token(tokens, token_i)
        
        if not token: raise error.UnmatchedBracketError(tokens[-1], expect)
        
        token_i += 1
        return token_i, FunctionNode(func_name, tokens[first_token:token_i], *func_args)
    
class NameNode(NodeBase):
    '''Represents a node with a name.'''
    tag = 'name'
    def __init__(self, name, tokens):
        '''Initialises a `NameNode`.'''
        super(NameNode, self).__init__(tokens)
        assert isinstance(name, str) and name, "name must be a string (" + repr(name) + ")"
        self.name = name.lower()
    
    def __str__(self): return self.name
    def __repr__(self): return self.tag + ':' + str(self)

class TextNode(NodeBase):
    '''Represents a node containing text.'''
    tag = 'text'
    def __init__(self, text, tokens):
        '''Initialises a `TextNode`.'''
        super(TextNode, self).__init__(tokens)
        self.text = text
    
    def __str__(self): return "'" + self.text + "'"
    def __repr__(self): return self.tag + ':' + str(self)

class ValueNode(NodeBase):
    '''Represents a node containing an immediate value.'''
    tag = 'value'
    def __init__(self, value, tokens):
        '''Initialises a `ValueNode`.'''
        super(ValueNode, self).__init__(tokens)
        self.value = value
    
    ConstantMap = {
        'TRUE': True,
        'FALSE': False,
        'NULL': None,
        'NONE': None,
    }
    
    @classmethod
    def parse(cls, tokens, first_token):
        '''Reads a `ValueNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        token_i = first_token
        token = _get_token(tokens, token_i)
        
        if not token:
            raise error.InvalidSyntaxError(tokens[-1])
        elif token.tag == 'number':
            token_i += 1
            try:
                return token_i, ValueNode(float(token.value), [token])
            except ValueError:
                raise error.InvalidNumberError(token, token.value)
        elif token.tag == 'constant':
            token_i += 1
            value = cls.ConstantMap.get(token.value, token.value)
            return token_i, ValueNode(value, [token])
        else:
            raise error.InvalidSyntaxError(token)
    
    def __str__(self):
        value_type = type(self.value).__name__
        return '%s <%s>' % (self.value, value_type)
    def __repr__(self): return self.tag + ':' + str(self)

class VariableNode(NameNode):
    '''Represents a variable.'''
    tag = 'variable'
    def __init__(self, name, tokens):
        super(VariableNode, self).__init__(name, tokens)
        self.implicit = False
        '''If ``True``, replace with `ValueNode` rather than raising a
        warning if the variable does not exist.
        '''
        self.external = False
        '''If ``True``, assume it is already initialised.'''
    
    @classmethod
    def parse(cls, tokens, first_token):
        '''Reads a `VariableNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        token_i = first_token
        token = _get_token(tokens, token_i)
        
        if not token: raise error.InvalidSyntaxError(tokens[-1])
        if token.tag != 'name': raise error.InvalidSyntaxError(token)
        
        var_name = token.value
        
        token_i += 1
        return token_i, VariableNode(var_name, tokens[first_token:token_i])
    
    @classmethod
    def define_external(cls, name):
        '''Creates an external `VariableNode` from a string.'''
        tokens = [Token('name', name, 0, 0)]
        node = VariableNode(name, tokens)
        node.external = True
        return node
    
    def __str__(self):
        if self.external:
            return '$!' + super(VariableNode, self).__str__()
        elif self.implicit:
            return '$?' + super(VariableNode, self).__str__()
        else:
            return '$' + super(VariableNode, self).__str__()

class BacktickNode(TextNode):
    '''Represents a line of code that began with a backtick.'''
    tag = 'backtick'
    
    @classmethod
    def parse(cls, tokens, first_token):
        '''Reads a `BacktickNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        token_i = first_token
        token = _get_token(tokens, token_i)
        
        if not token: raise error.InvalidSyntaxError(tokens[-1])
        if token.tag != 'backtick': raise error.InvalidSyntaxError(token)
        
        token_i += 1
        return token_i, BacktickNode(token.value, [token])

class GroupNode(NodeBase):
    '''Represents a group. Groups may be specified with a size.'''
    tag = 'group'
    
    def __init__(self, group, size, tokens):
        '''Initialises a group node. `group` should be a `VariableNode`
        or `FunctionNode`.
        '''
        super(GroupNode, self).__init__(tokens)
        
        assert isinstance(group, NodeBase), "group must be an AST node (" + repr(type(group)) + ")"
        assert not size or isinstance(size, NodeBase), "size must be an AST node (" + repr(type(size)) + ")"
        
        if group.tag not in ('function', 'variable'):
            raise error.ExpectedGroupError(group.tokens)
        
        self.tag = 'group'
        if group.tag == 'function':
            if group.name.startswith(('_op_', '_uop_', '_assign', '_list', '_getattr', '_getitem', '_call')):
                raise error.ExpectedGroupError(group.tokens)
            self.tag = 'generator'
        self.group = group
        self.size = size
    
    @classmethod
    def parse(cls, tokens, first_token):
        '''Reads a `GroupNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        token_i = first_token
        
        token = _get_token(tokens, token_i)
        group_size = None
        token_i, group_name = UnknownNode.parse(tokens, token_i)
        token = _get_token(tokens, token_i)
        if token and token.tag == 'name':
            group_size = group_name
            token_i, group_name = UnknownNode.parse(tokens, token_i)
            token = _get_token(tokens, token_i)
        
        if group_name is None: raise error.ExpectedGroupError(tokens[-1])
        
        return token_i, GroupNode(group_name, group_size, tokens[first_token:token_i])
    
    def __str__(self):
        if self.size: return '%s %s' % (self.size, self.group)
        else: return str(self.group)
    
    def __repr__(self): return self.tag + ':' + str(self)

class FromSourceNode(NodeBase):
    '''Represents the source groups or generators of a FROM-SELECT
    statement.
    '''
    tag = 'fromsource'
    
    def __init__(self, source_list, tokens):
        super(FromSourceNode, self).__init__(tokens)
        assert isinstance(source_list, list) and source_list, \
            "source_list must be a list (" + repr(source_list) + ")"
        assert all(s.tag in ('group', 'generator') for s in source_list), \
            "source_list must contain groups and generators only (" + repr(source_list) + ")"
        self.sources = source_list
    
    def __str__(self):
        return '[' + ', '.join(str(s) for s in self.sources) + ']'
    
    def __repr__(self): return self.tag + ':' + str(self)


class FromNode(NodeBase):
    '''Represents a FROM-SELECT statement.'''
    tag = 'from'
    
    def __init__(self, source_list, destination_list, using, tokens):
        super(FromNode, self).__init__(tokens)
        assert isinstance(source_list, list) and source_list, \
            "source_list must be a list (" + str(type(source_list)) + ")"
        assert isinstance(destination_list, list) and destination_list, \
            "destination_list must be a list (" + str(type(destination_list)) + ")"
        assert isinstance(using, NodeBase) and using.tag in ('fromsource', 'function'), \
            "using must be a from-source node or a function"
        
        self.sources = source_list
        self.destinations = destination_list
        self.using = using
    
    @classmethod
    def parse(cls, tokens, first_token):    #pylint: disable=R0912,R0915
        '''Reads a `FromNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        token_i = first_token
        token = _get_token(tokens, token_i)
        if not token: raise error.InvalidSyntaxError(tokens[-1])
        if token.tag != 'FROM': raise error.InvalidSyntaxError(token)
        
        source_list = []
        token_i += 1
        token = _get_token(tokens, token_i)
        while token and token.tag != 'SELECT':
            token_i, group = GroupNode.parse(tokens, token_i)
            source_list.append(group)
            token = _get_token(tokens, token_i)
            if not token or token.tag != ',': break
            token_i += 1
            token = _get_token(tokens, token_i)
        
        if not token: raise error.ExpectedSelectError(tokens[-1])
        if token.tag != 'SELECT': raise error.ExpectedSelectError(token)
        if not source_list: raise error.ExpectedGroupError(token)
        using = FromSourceNode(source_list, tokens[first_token+1:token_i])
        
        dest_list = []
        token_i += 1
        token = _get_token(tokens, token_i)
        while token and token.tag != 'USING':
            token_i, group = GroupNode.parse(tokens, token_i)
            dest_list.append(group)
            token = _get_token(tokens, token_i)
            if not token or token.tag != ',': break
            token_i += 1
            token = _get_token(tokens, token_i)
        
        if not dest_list: raise error.ExpectedGroupError(token or tokens[-1])
        for dest in dest_list:
            if not dest.group: raise error.ExpectedGroupError(token or tokens[-1])
            if dest.tag == 'generator': raise error.GeneratorAsDestinationError(dest.group.tokens)
            elif dest.tag != 'group': raise error.ExpectedGroupError(dest.group.tokens)
        
        if not token:
            return token_i, FromNode(source_list, dest_list, using, tokens[first_token:token_i])
        if token.tag != 'USING': raise error.ExpectedUsingError(token)
        
        token_i += 1
        token = _get_token(tokens, token_i)
        
        if not token: raise error.ExpectedFilterError(tokens[-1])
        while token:
            token_i, using = FunctionNode.parse_maybe_variable(tokens, token_i, _source=using)
            token = _get_token(tokens, token_i)
            if not token: break
            if token.tag != ',': raise error.ExpectedCommaError(token)
            token_i += 1
            token = _get_token(tokens, token_i)
        
        return token_i, FromNode(source_list, dest_list, using, tokens[first_token:token_i])
        
    def __str__(self):
        return 'SELECT %s USING %s' % (
            ', '.join(str(d) for d in self.destinations),
            str(self.using)
        )
    
    def __repr__(self): return self.tag + ':' + str(self)

class JoinSourceNode(NodeBase):
    '''Represents the source group(s) of a JOIN-INTO statement.'''
    tag = 'joinsource'
    
    def __init__(self, source_list, tokens):
        super(JoinSourceNode, self).__init__(tokens)
        assert isinstance(source_list, list) and source_list, \
            "source_list must be a list (" + repr(source_list) + ")"
        
        self.sources = source_list
    
    def __str__(self):
        return '[' + ', '.join(str(s) for s in self.sources) + ']'
    
    def __repr__(self): return self.tag + ':' + str(self)

class JoinNode(NodeBase):
    '''Represents a JOIN-INTO statement.'''
    tag = 'join'
    
    def __init__(self, source_list, destination_list, using, tokens):
        super(JoinNode, self).__init__(tokens)
        
        assert isinstance(source_list, list) and source_list, \
            "source_list must be a list (" + repr(source_list) + ")"
        assert isinstance(destination_list, list) and destination_list, \
            "destination_list must be a list (" + repr(destination_list) + ")"
        
        self.sources = source_list
        self.destinations = destination_list
        self.using = using
    
    @classmethod
    def parse(cls, tokens, first_token):    #pylint: disable=R0912,R0915
        '''Reads a `JoinNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        token_i = first_token
        token = _get_token(tokens, token_i)
        if not token: raise error.InvalidSyntaxError(tokens[-1])
        if token.tag != 'JOIN': raise error.InvalidSyntaxError(token)
        
        source_list = []
        token_i += 1
        token = _get_token(tokens, token_i)
        while token and token.tag != 'INTO':
            token_i, group = GroupNode.parse(tokens, token_i)
            source_list.append(group)
            token = _get_token(tokens, token_i)
            if not token or token.tag != ',': break
            token_i += 1
            token = _get_token(tokens, token_i)
        if not token: raise error.ExpectedSelectError(tokens[-1])
        if token.tag != 'INTO': raise error.ExpectedIntoError(token)
        if not source_list: raise error.ExpectedGroupError(token)
        using = JoinSourceNode(source_list, None)
        
        dest_list = []
        token_i += 1
        token = _get_token(tokens, token_i)
        while token and token.tag != 'USING':
            token_i, group = GroupNode.parse(tokens, token_i)
            dest_list.append(group)
            token = _get_token(tokens, token_i)
            if not token or token.tag != ',': break
            token_i += 1
            token = _get_token(tokens, token_i)
        
        if not dest_list: raise error.ExpectedGroupError(token or tokens[-1])
        for dest in dest_list:
            if not dest.group: raise error.ExpectedGroupError(token or tokens[-1])
            if dest.tag == 'generator': raise error.GeneratorAsDestinationError(dest.group.tokens)
            elif dest.tag != 'group': raise error.ExpectedGroupError(dest.group.tokens)
        
        if not token:
            return token_i, JoinNode(source_list, dest_list, using, tokens[first_token:token_i])
        
        token_i += 1
        token = _get_token(tokens, token_i)
        if not token: raise error.ExpectedFilterError(tokens[-1])
        while token:
            token_i, using = FunctionNode.parse_maybe_variable(tokens, token_i, _source=using)
            token = _get_token(tokens, token_i)
            if not token: break
            if token.tag != ',': raise error.ExpectedCommaError(token)
            token_i += 1
            token = _get_token(tokens, token_i)
        
        return token_i, JoinNode(source_list, dest_list, using, tokens[first_token:token_i])
    
    def __str__(self):
        return 'INTO %s USING %s' % (
            ', '.join(str(d) for d in self.destinations),
            str(self.using)
        )
    
    def __repr__(self): return self.tag + ':' + str(self)

class EvalNode(NodeBase):
    '''Represents an EVAL or EVALUATE statement.'''
    tag = 'eval'
    
    def __init__(self, source_list, using_list, tokens):
        super(EvalNode, self).__init__(tokens)
        
        assert isinstance(source_list, list) and source_list, \
            "source_list must be a list (" + repr(source_list) + ")"
        assert not using_list or isinstance(using_list, list), \
            "using_list must be a list (" + repr(using_list) + ")"
        
        self.sources = source_list
        self.using = using_list
    
    @classmethod
    def parse(cls, tokens, first_token):
        '''Reads an `EvalNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        token_i = first_token
        token = _get_token(tokens, token_i)
        if not token: raise error.InvalidSyntaxError(tokens[-1])
        if token.tag != 'EVAL': raise error.InvalidSyntaxError(token)
        
        source_list = []
        token_i += 1
        token = _get_token(tokens, token_i)
        while token and token.tag != 'USING':
            token_i, group = GroupNode.parse(tokens, token_i)
            source_list.append(group)
            token = _get_token(tokens, token_i)
            if not token or token.tag != ',': break
            token_i += 1
            token = _get_token(tokens, token_i)
        
        if not token:
            if not source_list: raise error.ExpectedGroupError(tokens[-1])
            return token_i, EvalNode(source_list, [], tokens[first_token:token_i])
        
        if not source_list: raise error.ExpectedGroupError(token)
        for src in source_list:
            if not src.group: raise error.ExpectedGroupError(token)
            if src.group.tag != 'variable': raise error.ExpectedGroupError(src.group.tokens)
        
        using_list = []
        token_i += 1
        token = _get_token(tokens, token_i)
        while token:
            token_i, func = FunctionNode.parse_maybe_variable(tokens, token_i)
            using_list.append(func)
            token = _get_token(tokens, token_i)
            if not token or token.tag != ',': break
            token_i += 1
            token = _get_token(tokens, token_i)
        
        if token: raise error.ExpectedCommaError(token)
        if not using_list: raise error.ExpectedEvaluatorError(tokens[-1])
        
        return token_i, EvalNode(source_list, using_list, tokens[first_token:token_i])
    
    def __str__(self):
        if self.using:
            return 'EVAL %s USING %s' % (
                ', '.join(str(s) for s in self.sources),
                ', '.join(str(u) for u in self.using)
            )
        else:
            return 'EVAL %s' % (
                ', '.join(str(s) for s in self.sources)
            )
    
    def __repr__(self): return self.tag + ':' + str(self)

class YieldNode(NodeBase):
    '''Represents a YIELD statement.'''
    tag = 'yield'
    
    def __init__(self, source_list, tokens):
        super(YieldNode, self).__init__(tokens)
    
        assert isinstance(source_list, list) and source_list, \
            "source_list must be a list (" + repr(source_list) + ")"
        
        self.sources = source_list
    
    @classmethod
    def parse(cls, tokens, first_token):
        '''Reads a `YieldNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        token_i = first_token
        token = _get_token(tokens, token_i)
        if not token: raise error.InvalidSyntaxError(tokens[-1])
        if token.tag != 'YIELD': raise error.InvalidSyntaxError(token)
        
        source_list = []
        token_i += 1
        token = _get_token(tokens, token_i)
        while token:
            token_i, group = GroupNode.parse(tokens, token_i)
            source_list.append(group)
            token = _get_token(tokens, token_i)
            if not token or token.tag != ',': break
            token_i += 1
            token = _get_token(tokens, token_i)
        
        if not source_list: raise error.ExpectedGroupError(tokens[-1])
        if token: raise error.ExpectedCommaError(token)
        return token_i, YieldNode(source_list, tokens[first_token:token_i])
    
    def __str__(self):
        return 'YIELD %s' % (', '.join(str(s) for s in self.sources))
    
    def __repr__(self): return self.tag + ':' + str(self)


class BlockNode(NameNode):
    '''Represents a named block.'''
    tag = 'block'
    
    def __init__(self, name, index, tokens):
        super(BlockNode, self).__init__(name, tokens)
        
        self.children = []
        self.index = index
        self.variables_in = None    # used by Verifier
        self.variables_out = None   # used by Verifier
        self.groups_local = None    # used by Verifier
    
    def __str__(self):
        return 'BLOCK %s\n%s\nEND %s' % (self.name, '\n'.join(str(c) for c in self.children), self.name)

class RepeatNode(BlockNode):
    '''Represents a REPEAT block.'''
    tag = 'repeat'
    
    def __init__(self, count, tokens):
        super(RepeatNode, self).__init__('_repeat', None, tokens)
        
        self.count = count
    
    @classmethod
    def parse(cls, tokens, first_token):
        '''Reads a `RepeatNode` from `tokens`.'''
        assert tokens, "tokens must be provided"
        token_i = first_token
        token = _get_token(tokens, token_i)
        if not token: raise error.InvalidSyntaxError(tokens[-1])
        if token.tag != 'REPEAT': raise error.InvalidSyntaxError(token)
        
        token_i += 1
        token_i, count = UnknownNode.parse(tokens, token_i)
        
        return token_i, RepeatNode(count, tokens[first_token:token_i])
    
    def __str__(self):
        return 'REPEAT %s\n%s\nEND REPEAT' % (self.count, '\n'.join(str(c) for c in self.children))
    
    def __repr__(self): return self.tag + ':' + str(self)
