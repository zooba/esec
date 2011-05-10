'''Performs token identification within ESDL definitions.
'''
from __future__ import absolute_import
import re

def _re(expr):
    '''Shortcut for compiling regular expressions.'''
    return re.compile(expr, re.IGNORECASE)

TOKENS = [
    ("FROM",        'statement', _re(r"from\b")),
    ("SELECT",      'statement', _re(r"select\b")),
    ("JOIN",        'statement', _re(r"join\b")),
    ("INTO",        'statement', _re(r"into\b")),
    ("USING",       'statement', _re(r"using\b")),
    ("YIELD",       'statement', _re(r"yield\b")),
    ("EVAL",        'statement', _re(r"eval(uate)?\b")),
    ("BEGIN",       'statement', _re(r"begin\b")),
    ("REPEAT",      'statement', _re(r"repeat\b")),
    ("END",         'statement', _re(r"end\b")),
    ("TRUE",        'literal', _re(r"true\b")),
    ("FALSE",       'literal', _re(r"false\b")),
    ("NULL",        'literal', _re(r"(null|none)\b")),
#    ("IN",          'operator', _re(r"in\b")),
#    ("NOT",         'operator', _re(r"not\b")),
#    ("ASSERT",      'statement', _re(r"assert\b")),
#    ("AND",         'operator', _re(r"and\b")),
#    ("OR",          'operator', _re(r"or\b")),
#    ("LT",          'operator', _re(r"\<")),
#    ("LE",          'operator', _re(r"(\<=|=\<)")),
#    ("NE",          'operator', _re(r"!=")),
#    ("EQ",          'operator', _re(r"==")),
#    ("GT",          'operator', _re(r"\>")),
#    ("GE",          'operator', _re(r"(\>=|=\>)")),
    ("COMMENTS",    'comment', _re(r"(#|;|//).*")),
    ("NAME",        'name', _re(r"(?!\d)\w+")),
    ("NUMBER",      'number', _re(r"(\d+\.\d*|\d+|\.\d+)(e[-+]?\d+)?")),
    ("DOT",         'operator', _re(r"\.")),
    ("OPEN_PAR",    'operator', _re(r"\(")),
    ("CLOSE_PAR",   'operator', _re(r"\)")),
    ("OPEN_BRACKET", 'operator', _re(r"\[")),
    ("CLOSE_BRACKET", 'operator', _re(r"\]")),
    ("OPEN_BRACE",  'operator', _re(r"\{")),
    ("CLOSE_BRACE", 'operator', _re(r"\}")),
    ("ADD",         'operator', _re(r"\+")),
    ("SUB",         'operator', _re(r"-")),
    ("ASSIGN",      'operator', _re(r"=")),
    ("COMMA",       'operator', _re(r"\,")),
    ("MUL",         'operator', _re(r"\*")),
    ("DIV",         'operator', _re(r"\/")),
    ("MOD",         'operator', _re(r"\%")),
    ("POW",         'operator', _re(r"\^")),
    ("`",           'special', _re(r"`.*$")),
    ("CONTINUATION",'special', _re(r"\\\s*((#|;|//).*)?$")),
]

class Token(object):
    '''Represents a parsed token from an ESDL definition.'''
    def __init__(self, tag, ttype, value, line, col):
        '''Creates a token.
        
        :Parameters:
          tag : string
            An identifier for the type of token.
          
          ttype : string
            The general type of the token.
          
          value : string
            The raw text parsed into this token.
          
          line : int
            The line number of the source file where this token was
            found. The first list of a file is line 1.
          
          col : int
            The column number of the source line where this token was
            found. The first column of a line is column 1.
        '''
        self.tag = tag
        '''A string identifier for the type of the token.'''
        self.type = ttype
        '''The general type of the token.'''
        self.value = value
        '''The text parsed into this token.'''
        self.line = line
        '''The line of the original source file where this token was
        found. The first line of a file is line 1.'''
        self.col = col
        '''The column of the original source line where this token was
        found. The first column of a line is column 1.'''
    
    def __eq__(self, other):
        if type(other) is str: return False
        return (self.tag, self.value, self.line, self.col) == (other.tag, other.value, other.line, other.col)
    
    def __gt__(self, other): return (self.line, self.col) > (other.line, other.col)
    def __lt__(self, other): return (self.line, self.col) < (other.line, other.col)
    
    def __str__(self):
        if self.type == 'eos':
            return '<eos> (%d:%d)' % (self.line+1, self.col+1)
        else:
            return '%s (%d:%d)' % (self.value, self.line+1, self.col+1)
    
    def __repr__(self):
        if self.type == 'eos':
            return '<eos> (%d:%d)' % (self.line+1, self.col+1)
        else:
            return '<%s>%s (%d:%d)' % (self.tag, self.value, self.line+1, self.col+1)
    
    @classmethod
    def parse(cls, line, lineno, col):
        '''Parses a single token from a source line.
        
        Returns a `Token` instance and the next column to start reading
        from.
        
        :Parameters:
          line : str
            The line of text to read from.
          
          lineno : int
            The number of the line to associate with the token. This
            value is not relevant for parsing.
          
          col : int
            The character position to match at. Whitespace is ignored.
        '''
        while col < len(line) and line[col].isspace():
            col += 1
        
        if col >= len(line):
            return None, col
        
        for token_name, token_type, token_regex in TOKENS:
            match = token_regex.match(line, col)
            if match:
                start_col, end_col = match.span()
                return cls(token_name, token_type, match.group(), lineno, start_col), end_col
        
        return cls('error', 'error', line[col:], lineno, col), col


class TokenReader(object):
    '''Provides safe sequential reading and lookahead of a list of
    tokens.
    '''
    def __init__(self, tokens, skip_comments=False):
        self.tokens = tokens
        self.i = 0
        self.skip_comments = skip_comments
        self.i_stack = []
        
        if self.skip_comments:
            self.i = -1
            self.move_next()
    
    def __nonzero__(self):
        return 0 <= self.i < len(self.tokens)
    
    @property
    def rest(self):
        '''Returns a list containing the remaining tokens.'''
        return self.tokens[self.i:] if self else []
    
    @property
    def current(self):
        '''Returns the current token or ``None``.'''
        return self.tokens[self.i] if self else None
    
    @property
    def last(self):
        '''Returns the last token stored. Intended for use when a token
        is expected but none is found.
        '''
        return self.tokens[-1] if self.tokens else None
    
    def move_next(self):
        '''Advances to the next token. Returns `self` after advancing.
        If ``skip_comments`` was ``True``, tokens with tags beginning
        with ``'COMMENT'`` are skipped.
        '''
        self.i += 1
        if self.skip_comments:
            while self and self.current.tag.startswith('COMMENT'):
                self.i += 1
        return self
    
    @property
    def peek(self):
        '''Returns the next token. Behaves identically to
        ``self.move_next().current`` without modifying the position.
        '''
        self.push_location()
        tok = self.move_next().current
        self.pop_location()
        return tok
    
    def push_location(self):
        '''Stores the current location on a stack.'''
        self.i_stack.append(self.i)
    
    def pop_location(self):
        '''Restores the topmost location on the stack.'''
        self.i = self.i_stack.pop()
    
    def drop_location(self):
        '''Forgets the topmost location on the stack.'''
        self.i_stack.pop()


def tokenise(source):
    '''Returns a sequence of lines of tokens from a source file, string
    or list of strings.
    '''
    
    if not source:
        return [Token('EOS', 'end', '\\n', 1, 1)]
    
    if isinstance(source, str):
        source = iter(source.splitlines())
    
    if not hasattr(source, '__iter__'):
        return [Token('EOS', 'end', '\\n', 1, 1)]
    
    tokens = []
    for lineno, line in enumerate(source):
        col = 0
        tok, col = Token.parse(line, lineno, col)
        while tok:
            tokens.append(tok)
            if tok.type == 'error': col += 1
            tok, col = Token.parse(line, lineno, col)
        
        if tokens and tokens[-1].tag == 'CONTINUATION':
            tokens.pop()
            continue
        
        tokens.append(Token('EOS', 'end', '\\n', lineno, col))
    return tokens

if __name__ == '__main__':
    code = tokenise(r'''FROM random_real(length=2,lowest=-2.0,highest=2.0) SELECT (size) population
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
END GENERATION
    ''')
    
    print code
        
