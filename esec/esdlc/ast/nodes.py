'''Contains the `Node` class and the `DEFAULT_SYMBOLS` dictionary that
are used to build abstract syntax trees for ESDL systems.
'''
from copy import copy
import itertools
import esdlc.errors as error

SHOW_REFERENCES = False

class Node(object):
    '''Represents a raw node in an AST.
    '''
    def __init__(self, tag='', category='',
        defence=0, attack=0, power=None,
        references=None, left=None, right=None, parent=None):
        
        self.tag = tag
        assert tag is None or isinstance(tag, str)
        self.category = category
        self._defence = defence if power is None else power
        self._attack = attack if power is None else power
        
        self.references = [] if references is None else references
        self.tokens = []
        self.data = None
        self.left = left
        self.right = right
        self.parent = parent
        
        self.on_init()
    
    @property
    def attack(self):
        '''Returns the attack value for this node.'''
        return self._attack
    
    @attack.setter              #pylint: disable=E1101
    def attack(self, value):    #pylint: disable=E0102,C0111
        self._attack = value

    @property
    def defence(self):
        '''Returns the defence value for this node.'''
        return self._defence
    
    @defence.setter             #pylint: disable=E1101
    def defence(self, value):   #pylint: disable=E0102,C0111
        self._defence = value

    def beats(self, other):
        '''Determines whether this node should be positioned higher in
        the syntax tree than `other`.

        The default behaviour is for nodes with an `attack` that is
        equal to or higher than the other node's `defence` to be
        promoted.
        '''
        if other is None: return False
        return self.attack >= other.defence

    def on_init(self):
        '''Called by the initialiser. Makes it easier to provide extra
        initialisation without having the handle every parameter.
        '''
        pass
    
    @property
    def fulltokens(self):
        '''Returns all the tokens included by this node.'''
        return self._fulltokens()
        
    def _fulltokens(self):
        '''Returns all the tokens included by this node. This function
        may be called by other nodes as part of their `_fulltokens`
        method.
        '''
        all_tokens = self.tokens
        if self.left is not None:
            all_tokens = self.left._fulltokens() + all_tokens   #pylint: disable=W0212
        if self.right is not None:
            all_tokens = all_tokens + self.right._fulltokens()  #pylint: disable=W0212
        return all_tokens
    
    @property
    def text(self):
        '''Returns the original text making up this node.'''
        return ''.join(t.value for t in self.tokens)
    
    @property
    def rightmost(self):
        '''Returns the right-most child of this node. If this node has
        no children, returns ``self``.
        '''
        if self.right:
            return self.right.rightmost
        else:
            return self
    
    def parent_where(self, category=None, tag=None):
        '''Returns the nearest ancestor matching either or both
        `category` and `tag` conditions (tested with ``in``, rather
        than ``==``).
        
        :Returns:
            A tuple ``(matching parent, direction)``, where
            direction is ``'left'`` or ``'right'``, depending on which
            branch of the parent contains the original node. If the
            original node is the returned ancestor, the direction is
            ``None``. If no matching parent is found, both values are
            ``None``.
        '''
        direction = None
        node = self
        while (node is not None and
               (category is None or node.category not in category) and
               (tag is None or node.tag not in tag)):
            next_node = node.parent
            direction = (None if next_node is None else
                         'left' if next_node.left is node else
                         'right' if next_node.right is node else
                         None)
            node = next_node
        return node, direction
    
    def iter_list(self, value_category=None, delimiter_category={'comma'}):
        '''Iterates through a list delimited by nodes in category
        `delimiter_category`.
        '''
        if self.category in delimiter_category:
            if self.left:
                for i in self.left.iter_list(value_category, delimiter_category): yield i
            if self.right:
                for i in self.right.iter_list(value_category, delimiter_category): yield i
        elif value_category is None or self.category in value_category:
            yield self
    
    def __str__(self):
        return repr(self)
    
    def __repr__(self):
        loc = self.location()
        if self.data is not None:
            return '%s(%s) <%s,%s>%s' % (self.tag, self.data, loc[0] or '?', loc[1] or '?',
                                         self.references if SHOW_REFERENCES else '')
        else:
            return '%s <%s,%s>%s' % (self.tag, loc[0] or '?', loc[1] or '?',
                                     self.references if SHOW_REFERENCES else '')
    
    def location(self):
        '''Returns the start location of this node in the original
        source code.
        '''
        if self.tokens:
            return self.tokens[0].line + 1, self.tokens[0].col + 1
        else:
            return None, None
    
    def __eq__(self, other):
        try:
            return self.tag == other.tag and self.location() == other.location()
        except AttributeError:
            return False
    
    def copy(self, new_tag=None):
        '''Returns a new copy of this node with different children, references
        and (optionally) tag.
        '''
        return type(self)(
            tag=new_tag if new_tag is not None else self.tag,
            category=self.category,
            defence=self._defence, attack=self._attack,
            references=None,
            left=None, right=None, parent=None)
    
    def clone(self, token_at=None, keep_tokens=True):
        '''Returns an alias of this node that has different children but shared
        references.
        '''
        inst = copy(self)
        inst.left = None
        inst.right = None
        inst.parent = None
        if not keep_tokens: inst.tokens = []
        if token_at is not None: self.references.append(token_at)
        return inst
    
    def detach(self):
        '''Detaches `self` from its parent.
        '''
        if self.parent is not None:
            if self.parent.left is self: self.parent.left = None
            if self.parent.right is self: self.parent.right = None
            self.parent = None
        return self
    
    def clone_detach(self, new_parent=None):
        '''Returns an alias of the branch beginning at this node.
        '''
        inst = self.clone()
        if self.left is not None:
            inst.left = self.left.clone_detach(inst)
        if self.right is not None:
            inst.right = self.right.clone_detach(inst)
        inst.parent = new_parent
        inst.tokens = self.tokens
        return inst
    
    def read_tokens(self, ast, tokens, symbols):
        '''Optionally consumes extra tokens.
        '''
        pass
    
    def in_place(self, parent):
        '''Notifies the node that it has been placed in a tree. This
        method is allowed to mutate the node.
        '''
        pass

    def validate(self):
        '''Raises an error if invalid.
        '''
        pass
    
class BlockNode(Node):
    '''Represents a named node containing statements.'''
    
    def on_init(self):
        self.expr = None
        self.close = None
        
    #pylint: disable=W0201
    def _read_name(self, ast, tokens, symbols): #pylint: disable=W0613
        '''Reads the name of this block from the provided tokens.'''
        name = tokens.current
        if name is None:
            raise error.ExpectedBlockNameError([tokens.last])
        elif name.type != 'name':
            raise error.ExpectedBlockNameError([name])
        self.data = name.value
    
    def read_tokens(self, ast, tokens, symbols):
        try:
            self._read_name(ast, tokens, symbols)
            self.tokens.append(tokens.current)
        finally:
            while tokens and tokens.current and tokens.current.tag != 'EOS':
                self.tokens.append(tokens.current)
                tokens.move_next()
        
        self.expr = [stmt for stmt in ast.parse_while(tokens, symbols, self.defence) if stmt]
        for stmt in self.expr: stmt.parent = self
        self.close = ast.parse_if(tokens, symbols, category='end')
        
        if self.close is None:
            raise error.UnexpectedEndOfDefinitionError(tokens.last)
        if self.close.tag != 'END':
            raise error.UnmatchedBracketError(self.close.tokens, 
                { ')': '(', ']': '[', '}': '{' }.get(self.close.tag, self.close.tag))
        
        self.attack, self.defence = 15, 21

    def __str__(self):
        return '%s %s %s' % (self.tag, self.data, self.references if SHOW_REFERENCES else '')

class RepeatNode(BlockNode):
    '''Represents a repeated node containing statements.'''
    
    #pylint: disable=W0201
    def _read_name(self, ast, tokens, symbols):
        tokens.push_location()
        count_expr = ast.parse_while(tokens, symbols, None)
        tokens.pop_location()
        tokens.move_next()
        if len(count_expr) == 0 or count_expr[0] is None:
            raise error.ExpectedRepeatCountError([tokens.last])
        self.data = count_expr[0]
        self.data.parent = self

    def __str__(self):
        return '%s %s %s' % (self.tag, self.data, self.references if SHOW_REFERENCES else '')

class EndNode(Node):
    '''Represents an end-of-block node.'''
    def read_tokens(self, ast, tokens, symbols):
        while tokens and tokens.current and tokens.current.tag != 'EOS':
            tokens.move_next()

class ExprNode(Node):
    '''Represents a nested expression.'''

    def __init__(self, tag='', category='',     #pylint: disable=R0913
        defence=0, attack=0, power=None,
        references=None, left=None, right=None, parent=None,
        expected_close=None):
        super(ExprNode, self).__init__(tag=tag, category=category,
        defence=defence, attack=attack, power=power,
        references=references, left=left, right=right, parent=parent)
        
        self.expr = None
        self.close = None
        self.expected_close = expected_close
    
    def copy(self, new_tag=None):
        '''Returns a new copy of this node with different children, references
        and (optionally) tag.
        '''
        inst = super(ExprNode, self).copy(new_tag=new_tag)
        inst.expected_close = self.expected_close
        return inst
    
    def clone(self, token_at=None, keep_tokens=True):
        '''Returns an alias of this node that has different children but shared
        references.
        '''
        inst = super(ExprNode, self).clone(token_at=token_at, keep_tokens=keep_tokens)
        inst.expected_close = self.expected_close
        return inst
    
    #pylint: disable=W0201
    def read_tokens(self, ast, tokens, symbols):
        self.expr = [node for node in ast.parse_while(tokens, symbols, self.defence) if node]
        for node in self.expr: node.parent = self
        self.close = ast.parse_if(tokens, symbols, category='end')
        if self.close is None:
            raise error.UnmatchedBracketError(tokens.current or tokens.last, self.tag)
        elif self.expected_close:
            if self.close.tag not in self.expected_close:
                raise error.UnmatchedBracketError(self.close.tokens, self.tag)
        self.attack, self.defence = 15, 21
    
    def _fulltokens(self):
        #pylint: disable=W0212
        all_tokens = list(self.tokens)
        if self.left is not None: all_tokens = self.left._fulltokens() + all_tokens
        all_tokens.extend(itertools.chain.from_iterable(node._fulltokens() for node in self.expr))
        all_tokens.extend(self.close._fulltokens())
        if self.right is not None: all_tokens.extend(self.right._fulltokens())
        return all_tokens

class PotentialUnaryNode(Node):
    '''Represents a node that will act as a unary operator if possible.

    Unary operators will not be promoted beyond a node that already
    has a left-child, and once positioned the `defence` value drops
    to 23.
    '''
    def beats(self, other):
        '''Determines whether this node should be positioned higher in
        the syntax tree than `other`.

        The behaviour for potential unary nodes is to never beat a node
        that has a left-child but no right-child. Otherwise, the normal
        rules apply.
        '''
        if not other or other.left and not other.right: return False
        return super(PotentialUnaryNode, self).beats(other)

    @property
    def defence(self):
        '''Returns the defence value for this node. If this is acting
        as a unary operator (that is, it has no left-child), the
        defence is reduced to 23.
        '''
        if self.left is None:
            return 23
        else:
            return self._defence


DEFAULT_SYMBOLS = {
    "ADD" :             PotentialUnaryNode('+', 'op', power=50),
    "SUB" :             PotentialUnaryNode('-', 'op', power=50),
    "MUL" :             PotentialUnaryNode('*', 'op', power=40),
    "DIV" :             PotentialUnaryNode('/', 'op', power=40),
    "MOD" :             PotentialUnaryNode('%', 'op', power=30),
    "POW" :             Node('^', 'op', defence=31, attack=30),     # right associative
    
    " number" :         Node(None, 'number', defence=21, attack=20),
    " name" :           Node(None, 'name', defence=21, attack=20),
    " expr" :           Node(None, 'expr', defence=21, attack=15),
    
    "DOT" :             Node('.', 'dot', power=22),
    "COMMA" :           Node(',', 'comma', power=65),

    "TRUE" :            Node('True',  'literal', power=20),
    "FALSE" :           Node('False', 'literal', power=20),
    "NULL" :            Node('Null',  'literal', power=20),

    "ASSIGN" :          Node('=', 'assign', defence=60, attack=60),
    
    "OPEN_PAR" :        ExprNode('(', 'expr', defence=100, expected_close=')'),
    "CLOSE_PAR" :       Node(')', 'end', attack=100),
    "OPEN_BRACKET" :    ExprNode('[', 'expr', defence=100, expected_close=']'),
    "CLOSE_BRACKET" :   Node(']', 'end', attack=100),
    "OPEN_BRACE" :      ExprNode('{', 'expr', defence=100, expected_close='}'),
    "CLOSE_BRACE" :     Node('}', 'end', attack=100),
    
    "COMMENTS" :        None,
    "CONTINUATION" :    None,
    "EOS" :             Node('EOS', power=1000),
    "error" :           Node(None, power=0),
    
    "BEGIN" :           BlockNode('BEGIN', 'block', defence=100),
    "REPEAT" :          RepeatNode('REPEAT', 'block', defence=100),
    "END" :             EndNode('END', 'end', attack=100),
    
    "FROM" :            Node('FROM', 'FromStmt', power=70),
    "JOIN" :            Node('JOIN', 'JoinStmt', power=70),
    "YIELD" :           Node('YIELD', 'YieldStmt', power=70),
    "EVAL" :            Node('EVAL', 'EvalStmt', power=70),
    
    "SELECT" :          Node('SELECT', 'SelectStmt', power=80),
    "INTO" :            Node('INTO', 'IntoStmt', power=80),
    
    "USING" :           Node('USING', 'UsingStmt', power=85),

    " pragma" :         Node(None, 'pragma', power=1),
}

