'''Performs token identification within ESDL definitions.
'''
from __future__ import absolute_import

class Token(object):    #pylint: disable=R0903
    '''Represents a parsed token from an ESDL definition.'''
    def __init__(self, tag, value, line, col):
        '''Creates a token.
        
        :Parameters:
          tag : string
            An identifier for the type of token. Typical values include
            ``'number'``, ``'name'``, ``'constant'``, ``'comment'``. In
            some cases, the value of `value` may be used as the tag.
          
          value : string
            The raw text parsed into this token.
          
          line : int
            The line number of the source file where this token was found.
            The first list of a file is line 1.
          
          col : int
            The column number of the source line where this token was found.
            The first column of a line is column 1.
        '''
        self.tag = tag
        '''A string identifier for the type of the token.'''
        self.value = value
        '''The text parsed into this token.'''
        self.line = line
        '''The line of the original source file where this token was found.
        The first line of a file is line 1.'''
        self.col = col
        '''The column of the original source line where this token was found.
        The first column of a line is column 1.'''
    
    def __eq__(self, other):
        if type(other) is str: return False
        return (self.tag, self.value, self.line, self.col) == (other.tag, other.value, other.line, other.col)
    
    def __gt__(self, other): return (self.line, self.col) > (other.line, other.col)
    def __lt__(self, other): return (self.line, self.col) < (other.line, other.col)
    
    def __str__(self):
        if self.tag == 'eos':
            return '<eos> (%d:%d)' % (self.line, self.col)
        else:
            return '%s (%d:%d)' % (self.value, self.line, self.col)
    
    def __repr__(self):
        if self.tag == 'eos':
            return '<eos> (%d:%d)' % (self.line, self.col)
        elif self.tag != self.value:
            return '<%s>%s (%d:%d)' % (self.tag, self.value, self.line, self.col)
        else:
            return '<%s> (%d:%d)' % (self.tag, self.line, self.col)

def _tokenise(source):  #pylint: disable=R0912,R0915
    '''Returns a sequence of tokens from a single string.'''
    
    if not source or not isinstance(source, str):
        yield Token('eos', '\n', 1, 1)
        raise StopIteration
    
    mode = ''
    word = ''
    
    line = 1
    i_start = -1
    i = 0
    source = source.strip()
    while i <= len(source):
        char = source[i] if i < len(source) else ''
        
        if mode == '':
            if not char:
                i += 1
            elif char.isdigit():
                mode = 'number'
            elif char.isalpha() or char == '_':
                mode = 'name'
            elif char in '()[]{},+-*%^=':
                yield Token(char, char, line, i-i_start)
                i += 1
            elif char == '.':
                if i+1 < len(source) and source[i+1].isdigit():
                    mode = 'number'
                else:
                    yield Token(char, char, line, i-i_start)
                    i += 1
            elif char in ' \t\v':
                i += 1
            elif char in '#;':
                mode = 'comment'
            elif char == '`':
                mode = 'backtick'
                i += 1
            elif char == '/':
                if i+1 < len(source) and source[i+1] == '/':
                    mode = 'comment'
                else:
                    yield Token('/', '/', line, i-i_start)
                    i += 1
            elif char == '\\':
                yield Token('continue', '\\', line, i-i_start)
                i += 1
            elif char in '\r\n':
                yield Token('eos', '\n', line, i-i_start)
                if source[i:i+2] == '\r\n': i += 1
                i += 1
                line += 1
                i_start = i - 1
            else:
                yield Token('error', char, line, i-i_start)
                i += 1
        
        elif mode in ('comment', 'backtick'):
            if not char:
                i += 1
            elif char in '\r\n':
                yield Token(mode, word, line, i-i_start-len(word))
                mode = ''
                word = ''
            else:
                word += char
                i += 1
        
        elif mode == 'number':
            if not char:
                yield Token(mode, word, line, i-i_start-len(word))
                mode = ''
                word = ''
                i += 1
            elif char.isdigit() or char in '.eE':
                word += char
                i += 1
            elif char in '+-' and word[-1] in 'eE':
                word += char
                i += 1
            else:
                yield Token(mode, word, line, i-i_start-len(word))
                mode = ''
                word = ''
        
        elif mode == 'name':
            if char.isalpha() or char.isdigit() or char and char in '_.':
                word += char
                i += 1
            else:
                word_up = word.upper()
                if word_up in ('FROM', 'SELECT', 'USING', 'JOIN', 'INTO', 'YIELD', 'BEGIN', 'REPEAT', 'END'):
                    mode = word_up
                elif word_up in ('EVAL', 'EVALUATE'):
                    mode = 'EVAL'
                elif word_up in ('TRUE', 'FALSE', 'NULL', 'NONE'):
                    mode = 'constant'
                    word = word_up
                yield Token(mode, word, line, i-i_start-len(word))
                mode = ''
                word = ''
    
    if mode in ('comment', 'backtick'):
        yield Token(mode, word, line, i-i_start-len(word))
    yield Token('eos', '\n', line, i-i_start)

def tokenise(source):
    '''Returns a sequence of lines of tokens from a source file, string
    or list of strings.
    '''
    if not source: raise ValueError("source must be provided.")
    
    if isinstance(source, file): source = ''.join(source)
    elif isinstance(source, list):
        if source[0][-1] in '\r\n': source = ''.join(source)
        else: source = '\n'.join(source)
    
    line = []
    continuation = False
    for token in _tokenise(source):
        if token.tag == 'eos':
            if continuation:
                continuation = False
            else:
                line.append(token)
                if line: yield line
                line = []
        elif token.tag == 'continue':
            continuation = True
        else:
            continuation = False
            line.append(token)
    if line: yield line

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
    
