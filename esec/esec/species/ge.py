'''Provides the `GESpecies` and `GEIndividual` classes for
Grammatical Evolution (GE) genomes.
'''
from esec.species.integer import IntegerSpecies, IntegerIndividual
from esec.utils import ConfigDict

# Override IntegerIndividual to provide one that ...
class GEIndividual(IntegerIndividual):
    '''An `Individual` for GE genomes.
    '''
    def __init__(self, genes, parent, bounds=None, grammar=None, defines=None, wrap_count=10, statistic=None):
        '''Initialises a new `GEIndividual`. Instances are generally
        created using the initialisation methods provided by
        `GESpecies`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          genes : iterable(int)
            The sequence of genes that make up the new individual.
          
          parent : `GEIndividual` or `Species`
            Either the `GEIndividual` that was used to generate the
            new individual, or an instance of `GESpecies`.
            
            If a `GEIndividual` is provided, the values for `bounds`,
            `grammar`, `defines` and `wrap_count` are taken from
            that.
          
          bounds : tuple ``(lower bound, upper bound)``
            The lower and upper limits on values that may be included
            in the genome. It is used to allow mutation operations to
            reintroduce values that are missing from the current
            genome and to maintain valid genomes.
          
          grammar : `Grammar` or dict
            The BNF grammar used to map integer genomes to Python
            programs.
          
          defines : string or dict
            A block of code or set of definitions to include at the
            start of every program.
          
          wrap_count : int |ge| 0 [defaults to 10]
            The number of times the genome may be reused when mapping
            to a phenome.
          
          statistic : dict [optional]
            A set of statistic values associated with this individual.
            These are accumulated with ``parent.statistic`` and allow
            statistics to accurately represent the population.
        '''
        
        self._phenome = None
        '''The cached, evaluated individual code.'''
        self._compiled = None
        '''The cached, compiled individual.'''
        self._effective_size = None
        '''The cached effective size of the individiual.'''
        if isinstance(grammar, dict):
            self.grammar = Grammar(grammar)
        elif isinstance(grammar, ConfigDict):
            self.grammar = Grammar(grammar.as_dict())
        else:
            self.grammar = grammar
        '''The grammar used for this individiual.'''
        self.defines = defines
        self.wrap_count = int(wrap_count)
        '''The number of times to reuse the genome when mapping.'''
        if isinstance(parent, GEIndividual):
            self.grammar = parent.grammar
            self.defines = parent.defines
            self.wrap_count = parent.wrap_count
        
        if isinstance(self.defines, str):
            defines = self.defines
            self.defines = { }
            '''The definitions used for this individual.'''
            exec defines in self.defines    #pylint: disable=W0122
        elif hasattr(self.defines, '__dict__'):
            self.defines = dict(self.defines.__dict__)
        elif not isinstance(self.defines, dict):
            self.defines = { }
        
        super(GEIndividual, self).__init__(genes, parent, bounds, statistic)
    
    @property
    def Eval(self): #pylint: disable=C0103
        '''A reference to a Python function represented in the program as
        ``Eval(...)``. If the program has not been previously compiled, it
        will be compiled at the first request.
        '''
        if not hasattr(self._compiled, '__call__'):
            defs = dict(self.defines)
            
            program, self._effective_size = self.grammar.eval(self.genome, self.wrap_count)
            self._phenome = program or ''
            
            if not program:
                self.statistic['did_not_compile'] = 1
                self.statistic['dnc_unterminated'] = 1
                self._compiled = None
                return self._compiled
            else:
                self.statistic['did_not_compile'] = 0
                self.statistic['dnc_unterminated'] = 0
            
            try:
                exec program in defs    #pylint: disable=W0122
                self._compiled = defs["Eval"]
                self.statistic['did_not_compile'] = 0
                self.statistic['dnc_exception'] = 0
            except KeyboardInterrupt:
                raise
            except:
                self.statistic['did_not_compile'] = 1
                self.statistic['dnc_exception'] = 1
                self._compiled = None
        
        return self._compiled
    
    @property
    def effective_size(self):
        '''Returns the number of codon (gene) values actually used when
        mapped to a program. This value may be larger than the length
        of the genome if `wrap_count` is greater than zero.'''
        if self._effective_size is None:
            _ = self.Eval
        return self._effective_size
    
    @property
    def phenome_string(self):
        '''Returns a multiline string containing the generated code for
        this individual.'''
        if self._phenome is None:
            _ = self.Eval
        return self._phenome
    
    @property
    def length_string(self):
        '''Returns a string containing the number of codons (genes)
        used when mapping this individual, followed by the number of
        codons in the individual.
        
        :Note:
            If `wrap_count` is greater than zero, the first number
            may be greater than the second.
        '''
        return '%d,%d' % (self.effective_size, len(self.genome))


class GESpecies(IntegerSpecies):
    '''Provides individuals with fixed- or variable-length genomes of
    integer values. Each gene is an integer between the provided
    ``lowest`` and ``highest`` values (inclusive).
    '''
    
    name = 'ge'
    
    def __init__(self, cfg, eval_default):
        super(GESpecies, self).__init__(cfg, eval_default)
        # Make some names public within the execution context
        self.public_context['random_ge'] = self.init_ge
    
    def init_ge(self, grammar, defines=None, length=None,
                      shortest=1, longest=100,
                      lowest=0, highest=255,
                      wrap_count=0):
        '''Returns instances of `GEIndividual` initialised with random values.
        
        The values of `lowest` and `highest` are stored with the individual and
        are used implicitly for mutation operations involving the individual.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          grammar : `Grammar` or dict
            The BNF grammar used to map integer genomes to Python
            programs.
          
          defines : string or dict
            A block of code or set of definitions to include at the
            start of every program.
          
          length : int > 0
            The number of genes to include in each individual. If left
            unspecified, a random number between `shortest` and
            `longest` (inclusive) is used to determine the length of
            each individual.
          
          shortest : int > 0
            The smallest number of genes in any individual.
          
          longest : int > `shortest`
            The largest number of genes in any individual.
          
          lowest : int
            The smallest value of any particular gene.
          
          highest : int > 'lowest'
            The largest value of any particular gene.
          
          wrap_count : int |ge| 0 [defaults to 10]
            The number of times the genome may be reused when mapping
            to a phenome.
        '''
        lowest = int(lowest)
        highest = int(highest)
        longest = int(longest)
        wrap_count = int(wrap_count)
        
        for indiv in self.init_random(length, shortest, longest, lowest, highest, None):
            yield GEIndividual(indiv.genome,            #pylint: disable=W0212
                               parent=self,
                               bounds=([lowest] * longest, [highest] * longest),
                               grammar=grammar,
                               defines=defines,
                               wrap_count=wrap_count)

class Grammar(object):
    '''GE grammar class.
    '''
    
    class _Rule(object):    #pylint: disable=R0903
        '''Represents a rule reference in a compiled `Grammar` object.
        '''
        __slots__ = ( 'name', )
        def __init__(self, name): self.name = name
        def __str__(self): return self.name
    
    def __init__(self, grammar):
        '''Initialises a new GE grammar.
        
        :Parameters:
          grammar : dict
            The a dictionary of rules. A rule with the key ``*`` must be
            included.
        
        Each key in `grammar` is the name of a rule; each value is a list of
        one or more rules. The grammar must resolve to valid Python code.
        
        The rule named ``*`` is used as the starting point.
        
        The rules ``TERMINAL``, ``NEWLINE``, ``INDENT``, ``INC_INDENT`` and
        ``DEC_INDENT`` are always defined.
        
        ``TERMINAL`` selects one of the inputs defined for the landscape.
        
        ``INDENT`` is replaced by the current indent level in spaces (1 space per indent).
        
        ``INC_INDENT`` and ``DEC_INDENT`` adjust the indent level.
        
        For example::
            
            {
                '*': [ '"def Eval(T):" NEWLINE INC_INDENT Body DEC_INDENT' ],
                'Body': [ 'INDENT Return NEWLINE', 'INDENT Line NEWLINE Body' ],
                'Line': [ 'Variable "=" Expr', '"if" Variable Comparison Variable ":" NEWLINE INDENT Body DEDENT' ],
                'Return': [ '"return" Expr' ],
                'Variable': [ '"V1"', '"V2"', '"V3"' ],
                'Expr': [ 'Source', '"(" Source BinaryOp Source ")"', '"(" UnaryOp Source ")"' ],
                'Source': [ 'TERMINAL', 'Variable', '"True"', '"False"' ],
                'UnaryOp': [ '"not"' ],
                'BinaryOp': [ '"and"', '"or"', '"xor"' ]
            }
        '''
        self.grammar = { }
        for key, value in grammar.iteritems():
            rules = [ ]
            for raw_rule in value:
                rule = [ ]
                literal = False
                text = ''
                for char in raw_rule:
                    if literal:
                        text += char
                        if char == '"':
                            literal = False
                            rule += [ text[:-1] ]
                            text = ''
                    else:
                        if char == '"':
                            literal = True
                        elif char == ' ':
                            if text:
                                rule += [ self._Rule(text) ]
                                text = ''
                        else:
                            text += char
                if text: rule += [ self._Rule(text) ]
                rules += [ rule ]
            
            self.grammar[key] = rules
        
        self.start = self._Rule('*')
    
    def __str__(self):
        result = ''
        
        for key, rules in self.grammar.iteritems():
            line = key + '\n    : '
            for rule in rules[:-1]:
                for rule_part in rule:
                    if isinstance(rule_part, self._Rule):line += rule_part.name + ' '
                    else: line += '"' + rule_part + '" '
                line += '\n    | '
            
            for rule_part in rules[-1]:
                if isinstance(rule_part, self._Rule): line += rule_part.name + ' '
                else: line += '"' + rule_part + '" '
            
            result += line + '\n\n'
        return result
    
    def eval(self, genome, wrap=0):
        '''Evaluates a given genome and returns the code produced by the
        sequence of codon values.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          genome : iterable(int)
            The set of codons to use to generate the program.
          
          wrap : int |ge| 0
            The maximum number of times `genome` may be reused. Genomes
            are reused when all values have been used but the grammar has
            not terminated. If the wrap count is exhausted without the
            grammar terminating, ``None`` is returned.
        
        :Returns:
            A tuple containing the program code (index zero) and the number
            of codon values used (index one).
        '''
        def _gen(genes, wrap_count):
            '''A generator that iterates through `genes` up to
            `wrap_count` times before terminating.'''
            for _ in xrange(wrap_count+1):
                for codon in genes:
                    yield codon
        
        eff_size = 0
        gen = _gen(genome, int(wrap))
        
        try:
            result = ''
            indent = 0
            stack = [ self.start ]
            while stack:
                if len(stack) > 500:
                    return (None, eff_size)
                rule = stack.pop()
                if type(rule) is not str:   # faster than isinstance() on CPython
                    assert isinstance(rule, self._Rule)
                    name = rule.name
                    if name == 'TERMINAL':
                        eff_size += 1
                        result += 'T[%d%%len(T)] ' % next(gen)
                    elif name == 'NEWLINE':
                        result += '\n'
                    elif name == 'INDENT':
                        result += ' ' * indent
                    elif name == 'INC_INDENT':
                        indent += 4
                    elif name == 'DEC_INDENT':
                        indent -= 4
                    else:
                        rules = self.grammar[name]
                        if len(rules) == 1:
                            stack.extend(reversed(rules[0]))
                        else:
                            eff_size += 1
                            codon = next(gen) % len(rules)
                            stack += reversed(rules[codon])
                else:
                    result += rule

            return (result, eff_size)
        except StopIteration:
            return (None, eff_size)
