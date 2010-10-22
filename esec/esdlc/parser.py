'''Provides `AST`, which converts a token sequence into an abstract
syntax tree.
'''
from __future__ import absolute_import
import esdlc.errors as error
from esdlc.lexer import tokenise
from esdlc.nodes import BlockNode, RepeatNode, UnknownNode


class AST(object):
    '''Represents an ESDL definition as a tree of nodes.
    '''
    def __init__(self):
        '''Initialises an empty AST.'''
        self.groups = set()
        self.globals = set()
        self.variables = set()
        self.constants = set()
        self.external_variables = set()
        self.init_block = None
        self.blocks = { }
        self.source_lines = []
        self._errors = []
        self.uninitialised = []
    
    @property
    def errors(self):
        '''Gets a list of errors found in the syntax tree.'''
        return [e for e in self._errors if not e.iswarning]
    
    @property
    def warnings(self):
        '''Gets a list of warnings found in the syntax tree.'''
        return self.get_warnings()
    
    def get_warnings(self, include_uninitialised=True):
        '''Gets a list of warnings found in the syntax tree.'''
        if include_uninitialised:
            return [e for e in self._errors if e.iswarning]
        else:
            return [e for e in self._errors if e.iswarning and \
                e.code not in (
                    error.UninitialisedGlobalError.code,
                    error.UninitialisedConstantError.code,
                    error.UninitialisedVariableError.code
                )
            ]
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    @classmethod
    def load(cls, filename):
        '''Creates an `AST` instance from a source file.
        '''
        with open(filename) as src:
            lines = list(src)
        return cls.parse(lines)
    
    @classmethod
    def parse(cls, source_lines):
        '''Creates an `AST` instance from source code.
        
        `source_lines` must be an iterable collection of lines of text, such
        as a file object, or a single string with embedded newline characters.
        '''
        self = AST()
        
        self.source_lines = lines = source_lines
        
        block_index = -1
        current_block = BlockNode('_init', block_index, 0)
        block_stack = []
        self.init_block = current_block
        
        for statement in tokenise(lines):
            try:
                statement = [t for t in statement if t.tag != 'comment']
                if not statement: continue
                token = statement[0]
                
                if current_block == None and token.tag not in ('BEGIN', 'eos'):
                    raise error.UnexpectedCommandError(token)
                
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                if token.tag == 'BEGIN':
                    if block_stack:
                        raise error.UnexpectedBlockNestingError(token)
                    
                    if len(statement) < 2 or statement[1].tag != 'name':
                        raise error.ExpectedBlockNameError(token)
                    
                    name = statement[1].value.lower()
                    block_index += 1
                    self.blocks[name] = current_block = BlockNode(name, block_index, [token])
                    block_stack.append(current_block)
                
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                elif token.tag == 'END':
                    if not block_stack: raise error.UnmatchedEndError(token)
                    last_block = block_stack.pop()
                    assert current_block is last_block, 'Inconsistent block_stack'
                    current_block = block_stack[-1] if block_stack else None
                
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                elif token.tag == 'REPEAT':
                    _, new_block = RepeatNode.parse(statement, 0)
                    current_block.children.append(new_block)
                    current_block = new_block
                    block_stack.append(current_block)
                
                # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                else:
                    i = 0
                    while i < len(statement):
                        #print
                        #print ' '.join(str(s) for s in statement[i:])
                        i, node = UnknownNode.parse(statement, i)
                        if node: current_block.children.append(node)
            except error.ESDLSyntaxErrorBase as ex:
                self._errors.append(ex)
        
        return self
