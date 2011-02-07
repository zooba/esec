'''Performs token identification within ESDL definitions.
'''
from __future__ import absolute_import

def _re(expr):
    '''Shortcut for compiling regular expressions.'''
    import re
    return re.compile(expr, re.IGNORECASE)

TOKENS = [
    ("FROM",        'statement', _re(r"from(?![a-z0-9_])")),
    ("SELECT",      'statement', _re(r"select(?![a-z0-9_])")),
    ("JOIN",        'statement', _re(r"join(?![a-z0-9_])")),
    ("INTO",        'statement', _re(r"into(?![a-z0-9_])")),
    ("USING",       'statement', _re(r"using(?![a-z0-9_])")),
    ("YIELD",       'statement', _re(r"yield(?![a-z0-9_])")),
    ("EVAL",        'statement', _re(r"eval(uate)?(?![a-z0-9_])")),
    ("BEGIN",       'statement', _re(r"begin(?![a-z0-9_])")),
    ("REPEAT",      'statement', _re(r"repeat(?![a-z0-9_])")),
    ("END",         'statement', _re(r"end(?![a-z0-9_])")),
    ("constant",    'literal', _re(r"(true|false|null|none)(?![a-z0-9_])")),

    ("comment",     'comment', _re(r"(#|;|//).*")),
    ("name",        'literal', _re(r"[a-z_][a-z0-9_]*")),
    ("number",      'literal', _re(r"([0-9]+\.[0-9]*|[0-9]+|\.[0-9]+)(e[-+]?[0-9]+)?")),
    (".",           'op', _re(r"\.")),
    ("(",           'op', _re(r"\(")),
    (")",           'op', _re(r"\)")),
    ("[",           'op', _re(r"\[")),
    ("]",           'op', _re(r"\]")),
    ("{",           'op', _re(r"\{")),
    ("}",           'op', _re(r"\}")),
    ("+",           'op', _re(r"\+")),
    ("-",           'op', _re(r"-")),
    ("=",           'op', _re(r"=")),
    (",",           'op', _re(r"\,")),
    ("*",           'op', _re(r"\*")),
    ("/",           'op', _re(r"\/")),
    ("%",           'op', _re(r"\%")),
    ("^",           'op', _re(r"\^")),
    ("backtick",    'special', _re(r"`.*")),
    ("continue",    'special', _re(r"\\\s*((#|;|//).*)?$")),
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
            return '<eos> (%d:%d)' % (self.line, self.col)
        else:
            return '%s (%d:%d)' % (self.value, self.line, self.col)
    
    def __repr__(self):
        if self.type == 'eos':
            return '<eos> (%d:%d)' % (self.line, self.col)
        else:
            return '<%s>%s (%d:%d)' % (self.tag, self.value, self.line, self.col)
    
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
                return cls(token_name, token_type, match.group(), lineno+1, start_col+1), end_col
        
        return cls('error', 'error', line[col:], lineno+1, col+1), col


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
    
    def move_next(self):
        '''Advances to the next token. Returns `self` after advancing.
        If ``skip_comments`` was ``True``, tokens with tags beginning
        with ``'COMMENT'`` are skipped.
        '''
        self.i += 1
        if self.skip_comments:
            while self and self.current.tag.startswith('comment'):
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
        yield [Token('eos', 'end', '\\n', 1, 1)]
        raise StopIteration
    
    if isinstance(source, str):
        source = iter(source.splitlines())
    
    if not hasattr(source, '__iter__'):
        yield [Token('eos', 'end', '\\n', 1, 1)]
        raise StopIteration
    
    tokens = []
    for lineno, line in enumerate(source):
        col = 0
        tok, col = Token.parse(line, lineno, col)
        while tok:
            tokens.append(tok)
            if tok.type == 'error': col += 1
            tok, col = Token.parse(line, lineno, col)
        
        if tokens and tokens[-1].tag == 'continue':
            tokens.pop()
            continue
        
        tokens.append(Token('eos', 'end', '\\n', lineno, col))
        yield tokens
        tokens = []

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
    
    for statement in code:
        print statement
        print
    
