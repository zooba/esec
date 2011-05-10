'''Provides the `AST` object for parsing a syntax tree from source
code.
'''

__all__ = ['parse', 'load']

import itertools
import esdlc.errors as error
import esdlc.ast.nodes
from esdlc.ast.validator import Validator

class AST(object):
    '''Produces an abstract syntax tree from source code.'''
    
    def __init__(self, tokens):
        self._errors = []
        
        symbols = dict((key, value.copy() if value else value) 
                       for key, value in esdlc.ast.nodes.DEFAULT_SYMBOLS.iteritems())
        self.expr = self.parse_while(tokens, symbols, 100)

        if tokens.current and tokens.current.type != 'eos':
            self._errors.append(error.InvalidSyntaxError(tokens.rest))

        validator = Validator()
        for stmt in self.expr:
            validator.validate(stmt)

        self._errors.extend(validator.errors)
    
    @property
    def errors(self):
        '''Returns errors found in the system definition.'''
        return [e for e in self._errors if not e.iswarning]
    
    @property
    def warnings(self):
        '''Returns warnings found for the system definition.'''
        return [e for e in self._errors if e.iswarning]
    
    def get_node(self, token, symbols):
        '''Returns the node for the specified token, creating a new one
        if necessary.
        '''
        if token is None:
            node = None
        elif token.type == 'name':
            node = symbols[" name"].copy(new_tag=token.value)
        elif token.type == 'number':
            try:
                key = repr(float(token.value))
                node = symbols[" number"].copy(new_tag=key)
            except ValueError:
                self._errors.append(error.InvalidNumberError([token], token.value))
                node = symbols[" error"]
        elif token.type == 'special' and token.tag == '`':
            node = symbols[" pragma"].copy(new_tag=token.value)
        else:
            node = symbols[token.tag]
        
        return node
    
    def parse_while(self, tokens, symbols, strength):
        '''Convert tokens into nodes while `strength` is not exceeded.
        '''
        result = []
        
        root = None
        current = None
        
        while tokens:
            node = self.get_node(tokens.current, symbols)
            while tokens and node is None:
                tokens.move_next()
                node = self.get_node(tokens.current, symbols)
            
            if node is None: break
            
            if node.tag == 'EOS':
                result.append(root)
                root = current = None
                tokens.move_next()
                if strength is None:
                    break
                else:
                    continue
            
            if strength is not None and node.attack >= strength: break
            
            node = node.clone(token_at=tokens.current, keep_tokens=False)
            node.tokens.append(tokens.current)
            tokens.move_next()
            
            try:
                node.read_tokens(self, tokens, symbols)
            except error.ESDLSyntaxErrorBase as ex:
                self._errors.append(ex)
            
            if root is None:
                current = root = node
                continue
            
            parent = current
            while node.beats(parent): # parent and parent.attack < node.defence:
                parent = parent.parent
            
            if parent is None:
                node.left = root
                node.left.parent = node
                root = node
            else:
                node.left = parent.right
                if node.left is not None: node.left.parent = node
                parent.right = node
                node.parent = parent
            
            node.in_place(node.parent)
            current = node
        
        if root:
            result.append(root)
            root = None
        return result
    
    def parse_if(self, tokens, symbols, tag=None, category=None):
        '''Reads exactly one node matching the specified tag and
        category.
        '''
        if not tokens: return None
        
        node = self.get_node(tokens.current, symbols)
        while tokens and node is None:
            tokens.move_next()
            node = self.get_node(tokens.current, symbols)
        
        if ((node is not None) and
            (tag is None or node.tag == tag) and
            (category is None or node.category == category)):
            node = node.clone(token_at=tokens.current, keep_tokens=False)
            node.tokens.append(tokens.current)
            tokens.move_next()
            node.read_tokens(self, tokens, symbols)
            return node
        else:
            return None
    
    def format(self):
        '''Returns a formatted string representation of the AST.
        '''
        result = []
        
        def _fmt(node, ind=''):
            '''Recursively formats the AST.'''
            if node is None:
                return
            elif isinstance(node, list):
                for i in node:
                    _fmt(i, ind)
                return
            elif node.category in {'expr', 'block'}:
                result.append(ind + '<' + (str(node)))
                _fmt(node.expr, ind+'  ')
                result.append(ind + '>' + (str(node.close) if node.close else "?"))
            else:
                result.append(ind + str(node).strip())
            _fmt(node.left, ind+'  ')
            _fmt(node.right, ind+'  ')
        
        _fmt(self.expr)
        
        return '\n'.join(result)

    def __str__(self):
        '''Returns an abbreivated string representation of the AST.
        '''
        result = []

        def _fmt(node):
            '''Recursively formats the AST.'''
            if node is None:
                return
            elif isinstance(node, list):
                for i in node:
                    _fmt(i)
                    result.append(';')
                if node: result.pop()
                return
            elif node.category == 'expr':
                result.extend(('<{', node.tag, '}'))
                _fmt(node.expr)
                result.extend(('{', node.close.tag if node.close else '?', '}>'))
            elif node.tag == 'BEGIN':
                result.extend(('<{', node.tag, ':', str(node.data or ''), '};'))
                _fmt(node.expr)
                result.extend((';{', node.close.tag if node.close else '?', '}>'))
            elif node.tag == 'REPEAT':
                result.extend(('<{', node.tag, ':'))
                _fmt(node.data)
                result.append('};')
                _fmt(node.expr)
                result.extend((';{', node.close.tag if node.close else '?', '}>'))
            else:
                result.append(node.tag)
            if node.left or node.right:
                result.append('{')
                _fmt(node.left)
                result.append(',')
                _fmt(node.right)
                result.append('}')

        _fmt(self.expr)
        
        return ''.join(result)


def parse(source):
    '''Loads an `AST` instance from the contents of `source`.'''
    from esdlc.ast.lexer import TokenReader
    tokens = TokenReader(esdlc.ast.lexer.tokenise(source))
        
    self = AST(tokens)
    return self

def load(path):
    '''Loads an `AST` instance from the contents of the file at
    `path`.
    '''
    with open(path) as src:
        return parse(src)
