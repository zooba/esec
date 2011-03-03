'''Provides the `BinaryIntegerIndividual` class for binary-valued genomes.
'''
from itertools import izip
from esec.individual import Individual
from esec.context import rand
from esec.species.binary import BinarySpecies

# Disabled: method could be a function, too many public methods
#pylint: disable=R0201,R0904

# Override Individual to provide a binary individual with a integer-valued phenotype.
class BinaryIntegerIndividual(Individual):
    '''An `Individual` for binary-valued genomes and integer-valued phenomes. Binary
    values are grouped into integer-valued parameters, summed and scaled.
    '''
    
    def __init__(self, genes, parent,
                 bits_per_value=None,
                 encoding=None,
                 statistic=None):
        '''Initialises a new individual.
        
        :Parameters:
          genes : iterable
            The sequence of genes that make up the new individual.
          
          parent : `BinaryIntegerIndividual` or `BinarySpecies`
            Either the `BinaryIntegerIndividual` that was used to generate
            the new individual, or the `BinarySpecies` descriptor that
            defines the type of individual.
            
            If a `BinaryIntegerIndividual` is provided, values for
            `bits_per_value` and `encoding` are taken from this individual.
          
          bits_per_value : list(int)
            The number of bits to use for each phenome value. If unspecified
            or ``None``, all bits in the individual contribute to a single
            value.
          
          encoding : int or function
            A function to convert from a binary genome to a int-valued
            phenome.
            
            The methods
            `BinaryIntegerSpecies.ones_complement_mapping`,
            `BinaryIntegerSpecies.twos_complement_mapping`,
            `BinaryIntegerSpecies.gray_code_mapping` and
            `BinaryIntegerSpecies.count_mapping` are provided for this
            parameter.
            
            If an integer is provided, it is mapped as follows:
          
          statistic : dict [optional]
            A set of statistic values associated with this individual.
            These are accumulated with ``parent.statistic`` and allow
            statistics to accurately represent the population.
        '''
        super(BinaryIntegerIndividual, self).__init__(genes, parent, statistic)
        
        self._phenome = None
        
        if isinstance(parent, BinaryIntegerIndividual):
            self.bits_per_value = parent.bits_per_value
            self.encoding = parent.encoding
            self.lower_bounds = parent.lower_bounds
            self.upper_bounds = parent.upper_bounds
        else:
            self.bits_per_value = bits_per_value
            self.encoding = encoding or self.count_mapping
            
            genes = self.genome
            self._phenome = None
            self.genome = [0] * len(genes)
            self.lower_bounds = self.phenome
            self._phenome = None
            self.genome = [1] * len(genes)
            self.upper_bounds = self.phenome
            self._phenome = None
            self.genome = genes
        
        assert isinstance(self.bits_per_value, list), "bits_per_value is not a list"
    
    @property
    def phenome(self):
        '''Returns the phenome of this individual.
        '''
        if not self._phenome:
            _genes = [ ]
            i = 0
            for bits in self.bits_per_value:
                if i + bits > len(self.genome): break
                _genes.append(self.genome[i:i+bits])
                i += bits
            self._phenome = list(self.encoding(_genes))
        return self._phenome
    
    @property
    def phenome_string(self):
        '''Returns a string representation of the phenome of this individual.
        '''
        if self._eval and hasattr(self._eval, 'phenome_string'):
            try: return self._eval.phenome_string(self)
            except AttributeError: pass
        return '[' + ', '.join('%f' % i for i in self.phenome) + ']'

class BinaryIntegerSpecies(BinarySpecies):
    '''Provides individuals with fixed- or variable-length genomes of
    binary values that map transparently to int values. Each gene has
    the value ``0`` or ``1``.
    '''
    
    name = 'Integer (Binary)'
    
    def __init__(self, cfg, eval_default):
        super(BinaryIntegerSpecies, self).__init__(cfg, eval_default)
        # Make some names public within the execution context
        self.public_context['random_int_binary'] = self.init_random_int
        self.public_context['binary_zero_int'] = self.init_zero_int
        self.public_context['binary_one_int'] = self.init_one_int
        
        # disable length-varying commands
        self.mutate_insert = None
        self.mutate_delete = None
    
    def legal(self, indiv):
        '''Determines whether `indiv` is legal.'''
        assert isinstance(indiv, BinaryIntegerIndividual), "Expected BinaryIntegerIndividual"
        return all(p in (0, 1) for p in indiv)
    
    @classmethod
    def ones_complement_mapping(cls, genes):
        '''Converts a list of gene blocks into a list of integer values
        using a ones-complement mapping.
        '''
        def _factor_iter():
            '''Yields an infinite sequence of integer values where
            each value is double the previous value. The first
            value is 1.'''
            factor = 1
            while True:
                yield factor
                factor += factor
        
        for gene in genes:
            yield sum(i * f for i, f in izip(reversed(gene), _factor_iter()))
    
    @classmethod
    def twos_complement_mapping(cls, genes):
        '''Converts a list of gene blocks into a list of integer values
        using a twos-complement mapping.
        '''
        def _factor_iter():
            '''Yields an infinite sequence of integer values where
            each value is double the previous value. The first
            value is 1.'''
            factor = 1
            while True:
                yield factor
                factor += factor
        
        for gene in genes:
            gene_parts = list(izip(reversed(gene), _factor_iter()))
            gene_parts[-1] = (gene_parts[-1][0], -gene_parts[-1][1])
            value = sum(i * f for i, f in gene_parts)
            yield value
    
    @classmethod
    def gray_code_mapping(cls, genes):
        '''Converts a list of gene blocks into a list of integer values
        using Gray coding.
        '''
        def _decode(gene):
            '''Decodes Gray coded gene blocks into regular binary.'''
            last_value = 0
            new_gene = []
            for i in gene:
                last_value ^= i
                new_gene.append(last_value)
            return new_gene
            
        return cls.ones_complement_mapping(_decode(gene) for gene in genes)
    
    @classmethod
    def count_mapping(cls, genes):
        '''Converts a list of gene blocks into a list of integer values
        by counting the number of 1 bits.
        '''
        return (sum(gene) for gene in genes)
    
    
    def _init(self, length, bits_per_value,
              ones_complement, twos_complement, gray_code, counted, encoding,   #pylint: disable=W0613
              _gen):
        '''All parameters have the same meaning as for `init_random_int`.'''
        assert length is not True, "length has no value"
        assert bits_per_value is not True, "bits_per_value has no value"
        assert encoding is not True, "encoding has no value"
        
        if hasattr(length, 'get'): length = length.get('exact', length.get('max'))
        length = int(length or 0)
        assert length, "length must be specified"
        
        if not encoding:
            encoding = BinaryIntegerSpecies.count_mapping
            if ones_complement: encoding = BinaryIntegerSpecies.ones_complement_mapping
            elif twos_complement: encoding = BinaryIntegerSpecies.twos_complement_mapping
            elif gray_code: encoding = BinaryIntegerSpecies.gray_code_mapping
        elif isinstance(encoding, int):
            encoding = {
                1: BinaryIntegerSpecies.ones_complement_mapping,
                2: BinaryIntegerSpecies.twos_complement_mapping,
                3: BinaryIntegerSpecies.gray_code_mapping
            }.get(encoding, BinaryIntegerSpecies.gray_code_mapping)
        
        assert hasattr(encoding, '__call__'), "encoding must be callable"
        assert bits_per_value, "bits_per_value must be specified"
        if hasattr(bits_per_value, '__iter__'):
            bits_per_value = [int(i) for i in bits_per_value]
        else:
            bits_per_value = [int(bits_per_value)] * length
        
        indiv_len = sum(bits_per_value)
        
        while True:
            yield BinaryIntegerIndividual([_gen(i) for i in xrange(indiv_len)],
                                          self,
                                          bits_per_value=bits_per_value,
                                          encoding=encoding)
    
    
    def init_random_int(self,
                        length=None,
                        bits_per_value=8,
                        ones_complement=False, twos_complement=False,
                        gray_code=False, counted=False,
                        encoding=None):
        '''Returns instances of `BinaryIntegerIndividual` initialised with random bitstrings.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          length : int > 0
            The number of int values to include in each individual.
            The number of bits is determined by the sum of
            `bits_per_value`. If omitted, the number of values is
            determined by the length of `bits_per_value`.
          
          bits_per_value : int or iterable(int) [default 8]
            The number of bits to use for each phenome value. If an int
            value is passed, it is used for every value.
          
          ones_complement : bool
            If ``True``, ones-complement encoding is used.
          
          twos_complement : bool
            If ``True``, twos-complement encoding is used.
          
          gray_code : bool
            If ``True``, a Gray code encoding is used.
          
          counted : bool
            If ``True``, a bit-counting encoding is used. This is the
            default if no encoding scheme is selected.
          
          encoding : int or function
            A function taking a sequence of lists of binary genes and
            returning an integer.
            
            If an integer is provided, it is mapped as follows:
                0 |rArr| `BinaryIntegerSpecies.count_mapping`
                
                1 |rArr| `BinaryIntegerSpecies.ones_complement_mapping`
                
                2 |rArr| `BinaryIntegerSpecies.twos_complement_mapping`
                
                3 |rArr| `BinaryIntegerSpecies.gray_code_mapping`
            
            Any other value is mapped to
            `BinaryIntegerSpecies.count_mapping`.
            
            If provided, this value is used instead of the
            `ones_complement`, `twos_complement`, `gray_code` and
            `counted` parameters.
        '''
        return self._init(length, bits_per_value,
                          ones_complement, twos_complement, gray_code, counted, encoding,
                          lambda _: 0 if rand.random() < 0.5 else 1)
    
    def init_zero_int(self,
                      length=None,
                      bits_per_value=8,
                      ones_complement=False, twos_complement=False,
                      gray_code=False, counted=False,
                      encoding=None):
        '''Returns instances of `BinaryIntegerIndividual` initialised with zeros.
        
        Parameters are the same as for `init_random_int`.
        '''
        return self._init(length, bits_per_value,
                          ones_complement, twos_complement, gray_code, counted, encoding,
                          lambda _: 0)
    
    def init_one_int(self,
                     length=None,
                     bits_per_value=8,
                     ones_complement=False, twos_complement=False,
                     gray_code=False, counted=False,
                     encoding=None):
        '''Returns instances of `BinaryIntegerIndividual` initialised with ones.
        
        Parameters are the same as for `init_random_int`.
        '''
        return self._init(length, bits_per_value,
                          ones_complement, twos_complement, gray_code, counted, encoding,
                          lambda _: 1)
