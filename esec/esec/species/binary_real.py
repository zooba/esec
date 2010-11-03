'''Provides the `BinaryRealIndividual` class for binary-valued genomes.
'''
from itertools import izip as zip   #pylint: disable=W0622
from esec.individual import Individual
from esec.context import rand
from esec.species.binary import BinarySpecies

# Disabled: method could be a function, too many parameters
#pylint: disable=R0201,R0913

# Override Individual to provide a binary individual with a real-valued phenotype.
class BinaryRealIndividual(Individual):
    '''An `Individual` for binary-valued genomes and real-valued phenomes. Binary
    values are grouped into real-valued parameters, summed and scaled.
    '''
    
    def __init__(self, genes, parent,
                 bits_per_value=None,
                 lowest=0.0, highest=1.0,
                 encoding=None,
                 statistic=None):
        '''Initialises a new individual.
        
        :Parameters:
          genes : iterable
            The sequence of genes that make up the new individual.
          
          parent : `BinaryRealIndividual` or `BinarySpecies`
            Either the `BinaryRealIndividual` that was used to generate
            the new individual, or the `BinarySpecies` descriptor that
            defines the type of individual.
            
            If a `BinaryRealIndividual` is provided, values for
            `bits_per_value`, `lowest`, `highest` and `encoding` are taken
            from this individual.
          
          bits_per_value : list(int)
            The number of bits to use for each phenome value. If unspecified
            or ``None``, all bits in the individual contribute to a single
            value.
          
          lowest : list(float)
            The value of the minimum binary value for each real value.
            The actual binary value producing this depends on `encoding`.
            
          highest : list(float)
            The value of the minimum binary value for each real value.
            The actual binary value producing this depends on `encoding`.
          
          encoding : int or function
            A function to convert from a binary genome to a real-valued
            phenome.
            
            The methods
            `BinaryRealSpecies.ones_complement_mapping`,
            `BinaryRealSpecies.twos_complement_mapping`,
            `BinaryRealSpecies.gray_code_mapping` and
            `BinaryRealSpecies.count_mapping` are provided for this.
          
          statistic : dict [optional]
            A set of statistic values associated with this individual.
            These are accumulated with ``parent.statistic`` and allow
            statistics to accurately represent the population.
        '''
        super(BinaryRealIndividual, self).__init__(genes, parent, statistic)
        
        self._phenome = None
        
        if isinstance(parent, BinaryRealIndividual):
            self.bits_per_value = parent.bits_per_value
            self.lowest = parent.lowest
            self.highest = parent.highest
            self.encoding = parent.encoding
        else:
            self.bits_per_value = bits_per_value
            self.lowest = lowest
            self.highest = highest
            self.encoding = encoding or self.count_mapping
        
        assert isinstance(self.lowest, list), "lowest is not a list"
        assert isinstance(self.highest, list), "highest is not a list"
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
            self._phenome = list(self.encoding(_genes, self.lowest, self.highest))
        return self._phenome
    
    @property
    def phenome_string(self):
        '''Returns a string representation of the phenome of this individual.
        '''
        return '[' + ', '.join('%f' % i for i in self.phenome) + ']'

class BinaryRealSpecies(BinarySpecies):
    '''Provides individuals with fixed- or variable-length genomes of
    binary values that map transparently to real values. Each gene has
    the value ``0`` or ``1``.
    '''

    name = 'Real (Binary)'
    
    def __init__(self, cfg, eval_default):
        super(BinaryRealSpecies, self).__init__(cfg, eval_default)
        # Make some names public within the execution context
        self.public_context['random_real_binary'] = self.init_random_real
        self.public_context['binary_zero_real'] = self.init_zero_real
        self.public_context['binary_one_real'] = self.init_one_real
        
        # disable length-varying commands
        self.mutate_insert = None
        self.mutate_delete = None
    
    @classmethod
    def ones_complement_mapping(cls, genes, lowest, highest):
        '''Converts a list of gene blocks into a list of real values
        using a ones-complement mapping.
        '''
        def _factor_iter():
            '''Yields an infinite sequence of floating point values where
            each value is half the previous value. The first value is 0.5.'''
            factor = 1.0
            while True:
                factor *= 0.5
                yield factor
        
        for gene, low, high in zip(genes, lowest, highest):
            mapped = [(i*f, f) for i, f in zip(gene, _factor_iter())]
            value = sum(i[0] for i in mapped) / sum(i[1] for i in mapped)
            yield (high - low) * value + low
    
    @classmethod
    def twos_complement_mapping(cls, genes, lowest, highest):
        '''Converts a list of gene blocks into a list of real values
        using a twos-complement mapping.
        '''
        def _factor_iter():
            '''Yields an infinite sequence of floating point values where
            each value is half the previous value. The first value is 0.5.'''
            factor = 1.0
            while True:
                factor *= 0.5
                yield factor
        
        for gene, low, high in zip(genes, lowest, highest):
            temp_gene = list(gene)
            temp_gene[0] = 1 - temp_gene[0]
            mapped = [(i * f, f) for i, f in zip(temp_gene, _factor_iter())]
            value = sum(i[0] for i in mapped) / sum(i[1] for i in mapped)
            yield (high - low) * value + low
    
    @classmethod
    def gray_code_mapping(cls, genes, lowest, highest):
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
            
        return cls.ones_complement_mapping((_decode(gene) for gene in genes), lowest, highest)
    
    @classmethod
    def count_mapping(cls, genes, lowest, highest):
        '''Converts a list of gene blocks into a list of real values
        by scaling the number of 1 bits.
        '''
        for gene, low, high in zip(genes, lowest, highest):
            res = (high - low) / len(gene)
            yield res * sum(gene) + low
    
    
    def _init(self, length, bits_per_value, lowest, highest, resolution, offset,
              ones_complement, twos_complement, gray_code, counted, encoding,   #pylint: disable=W0613
              _gen):
        '''All parameters have the same meaning as for `init_random_real`.'''
        
        if hasattr(length, 'get'): length = length.get('exact', length.get('max'))
        length = int(length or 0)
        assert length, "length must be specified"
        
        if not encoding:
            encoding = BinaryRealSpecies.count_mapping
            if ones_complement: encoding = BinaryRealSpecies.ones_complement_mapping
            elif twos_complement: encoding = BinaryRealSpecies.twos_complement_mapping
            elif gray_code: encoding = BinaryRealSpecies.gray_code_mapping
        elif isinstance(encoding, int):
            encoding = {
                1: BinaryRealSpecies.ones_complement_mapping,
                2: BinaryRealSpecies.twos_complement_mapping,
                3: BinaryRealSpecies.gray_code_mapping
            }.get(encoding, BinaryRealSpecies.gray_code_mapping)
        
        assert hasattr(encoding, '__call__'), "encoding must be callable"
        assert bits_per_value, "bits_per_value must be specified"
        if hasattr(bits_per_value, '__iter__'):
            bits_per_value = [int(i) for i in bits_per_value]
        else:
            bits_per_value = [int(bits_per_value)] * length
        
        if offset is not None and resolution is not None:
            lowest = [float(offset)] * length
            highest = [float(resolution) * i for i in bits_per_value]
        else:
            assert lowest is not None, "lowest must be specified"
            assert highest is not None, "highest must be specified"
            
            if hasattr(lowest, '__iter__'):
                lowest = [float(i) for i in lowest]
            else:
                lowest = [float(lowest)] * length
            if hasattr(highest, '__iter__'):
                highest = [float(i) for i in highest]
            else:
                highest = [float(highest)] * length
        
        indiv_len = sum(bits_per_value)
        
        while True:
            yield BinaryRealIndividual([_gen(i) for i in xrange(indiv_len)], self, \
                                       bits_per_value=bits_per_value,
                                       lowest=lowest, highest=highest,
                                       encoding=encoding)
    
    
    def init_random_real(self,
                         length=None,
                         bits_per_value=8,
                         lowest=0.0, highest=1.0,
                         resolution=None, offset=None,
                         ones_complement=False, twos_complement=False,
                         gray_code=False, counted=False,
                         encoding=None):
        '''Returns instances of `BinaryRealIndividual` initialised with random bitstrings.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          length : int > 0
            The number of real values to include in each individual.
            The number of bits is determined by the sum of
            `bits_per_value`. If omitted, the number of values is
            determined by the length of `bits_per_value`.
          
          bits_per_value : int or iterable(int) [default 8]
            The number of bits to use for each phenome value. If an int
            value is passed, it is used for every value.
          
          lowest : float or iterable(float) [default 0.0]
            The lowest real value to map to.
            
            If `resolution` and `offset` are provided, these values are
            used instead of `lowest` and `highest`.
          
          highest : float or iterable(float) [default 1.0]
            The exclusive highest real value to map to. This value will
            never be produced
            
            If `resolution` and `offset` are provided, these values are
            used instead of `lowest` and `highest`.
          
          resolution : float [optional]
            The amount each ``1`` bit contributes to its phenome value.
            
            `resolution` is ignored unless `offset` is also specified.
          
          offset : float [optional]
            The lowest real value to map to.
            
            `offset` is ignored unless `resolution` is also specified.
          
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
                0 |rArr| `BinaryRealSpecies.count_mapping`
                
                1 |rArr| `BinaryRealSpecies.ones_complement_mapping`
                
                2 |rArr| `BinaryRealSpecies.twos_complement_mapping`
                
                3 |rArr| `BinaryRealSpecies.gray_code_mapping`
            
            Any other value is mapped to
            `BinaryRealSpecies.count_mapping`.
            
            If provided, this value is used instead of the
            `ones_complement`, `twos_complement`, `gray_code` and
            `counted` parameters.
        '''
        return self._init(length, bits_per_value, lowest, highest, resolution, offset,
                          ones_complement, twos_complement, gray_code, counted, encoding,
                          lambda _: 0 if rand.random() < 0.5 else 1)
    
    def init_zero_real(self,
                         length=None,
                         bits_per_value=8,
                         lowest=0.0, highest=1.0,
                         resolution=None, offset=None,
                         ones_complement=False, twos_complement=False,
                         gray_code=False, counted=False,
                         encoding=None):
        '''Returns instances of `BinaryRealIndividual` initialised with zeros.
        
        Parameters are the same as for `init_random_real`.
        '''
        return self._init(length, bits_per_value, lowest, highest, resolution, offset,
                          ones_complement, twos_complement, gray_code, counted, encoding,
                          lambda _: 0)
    
    def init_one_real(self,
                         length=None,
                         bits_per_value=8,
                         lowest=0.0, highest=1.0,
                         resolution=None, offset=None,
                         ones_complement=False, twos_complement=False,
                         gray_code=False, counted=False,
                         encoding=None):
        '''Returns instances of `BinaryRealIndividual` initialised with ones.
        
        Parameters are the same as for `init_random_real`.
        '''
        return self._init(length, bits_per_value, lowest, highest, resolution, offset,
                          ones_complement, twos_complement, gray_code, counted, encoding,
                          lambda _: 1)
