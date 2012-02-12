'''Performs token identification within ESDL definitions.
'''
from __future__ import absolute_import
import re

def _re(expr):
    '''Shortcut for compiling regular expressions.'''
    return re.compile(expr, re.IGNORECASE)

def _escape(s):
    return ('\\' + s) if s in r'()[]{}.,!@#$%^&*/=\?+|' else s

def _any(strings):
    '''Shortcut for compiling regular expressions from a list of
    strings.'''
    return re.compile('(' + '|'.join(_escape(s) for s in strings) + ')', re.IGNORECASE)

TOKENS = [
    ('comment', _re(r"(#|;|//).*")),
    #('comparison', _any(('<=', '=<', '<', '!=', '==', '>', '>=', '=>'))),
    ('operator', _any('+-*/%^.')),
    ('assign', _re('\\=')),
    ('comma', _re('\\,')),
    ('name', _re(r"(?!\d)\w+")),
    ('number', _re(r"(\d+\.\d*|\d+|\.\d+)(e[-+]?\d+)?")),
    ('open', _any('([{')),
    ('close', _any(')]}')),
    ('pragma', _re(r"`.*$")),
    ('skip_eos', _re(r"\\\s*((#|;|//).*)?$")),
]

class Token(object):
    '''Represents a parsed token from an ESDL definition.'''
    def __init__(self, tag, value, line, col):
        '''Creates a token.
        
        :Parameters:
          tag : string
            An identifier for the type of token.
          
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
        self.value = value
        '''The text parsed into this token.'''
        if self.tag not in ('pragma', 'comment'):
            self.value = self.value.lower()

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
        return '%s (%d:%d)' % (self.value, self.line+1, self.col+1)
    
    def __repr__(self):
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
        
        for token_tag, token_regex in TOKENS:
            match = token_regex.match(line, col)
            if match:
                start_col, end_col = match.span()
                return cls(token_tag, match.group(), lineno, start_col), end_col
        
        return cls('error', line[col:], lineno, col), col


class TokenReader(object):
    '''Provides safe sequential reading and lookahead of a list of
    tokens.
    '''
    def __init__(self, tokens, skip_comments=False):
        self.tokens = tokens
        self.i = 0
        self.skip_comments = skip_comments
        self.i_stack = []
        self.token_stack = []
        
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
    
    def move_next(self, update_stacks=True):
        '''Advances to the next token. Returns `self` after advancing.
        If ``skip_comments`` was ``True``, tokens with tags beginning
        with ``'COMMENT'`` are skipped.
        '''
        self.i += 1
        if self.skip_comments:
            while self and self.current.tag.startswith('comment'):
                if update_stacks:
                    for stack in self.token_stack:
                        stack.append(self.current)
                self.i += 1

        if self and update_stacks:
            for stack in self.token_stack:
                stack.append(self.current)
        return self
    
    @property
    def peek(self):
        '''Returns the next token. Behaves identically to
        ``self.move_next().current`` without modifying the position.
        '''
        self.push_location()
        tok = self.move_next(False).current
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
    
    def push_tokenset(self):
        '''Starts caching tokens from here onwards.'''
        self.token_stack.append([self.current])
    
    def pop_tokenset(self):
        '''Returns the most recent token set.'''
        return self.token_stack.pop()
    
    def drop_tokenset(self):
        '''Forgets the most recent token set.'''
        self.token_stack.pop()


def tokenise(source):
    '''Returns a sequence of lines of tokens from a source file, string
    or list of strings.
    '''
    
    if not source:
        return [Token('eos', '', 1, 1)]
    
    if isinstance(source, str):
        source = iter(source.splitlines())
    
    if not hasattr(source, '__iter__'):
        return [Token('eos', '', 1, 1)]
    
    tokens = []
    for lineno, line in enumerate(source):
        col = 0
        tok, col = Token.parse(line, lineno, col)
        while tok:
            tokens.append(tok)
            if tok.tag == 'error': col += 1
            tok, col = Token.parse(line, lineno, col)
        
        if tokens and tokens[-1].tag == 'skip_eos':
            tokens.pop()
            continue
        
        tokens.append(Token('eos', '', lineno, col))
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
    
    for i in code:
        if i.tag == 'eos':
            print
        else:
            print repr(i),
        
