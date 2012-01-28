'''Provides the `SequenceSpecies` and `SequenceIndividual` classes for
sequencing genomes.
'''
import collections
from itertools import izip, islice, chain
from esec.species import Species
from esec.individual import Individual
from esec.context import rand
import esec.species

# Disabled: method could be a function, too many public methods
#pylint: disable=R0201,R0904

# Override Individual to provide one that keeps a validator with it
class SequenceIndividual(Individual):
    '''An `Individual` for sequence genomes.
    '''
    def __init__(self, genes, parent, statistic=None):
        '''Initialises a new `SequenceIndividual`. Instances are
        generally created using the initialisation methods provided by
        `SequenceSpecies`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          genes : iterable(int)
            The sequence of genes that make up the new individual.
          
          parent : `SequenceIndividual` or `SequenceSpecies`
            Either the `SequenceIndividual` that was used to generate
            the new individual, or an instance of `SequenceSpecies`.
            
            If a `SequenceIndividual` is provided, its value for
            `item_count` is used instead of the parameters provided.
          
          statistic : dict [optional]
            A set of statistic values associated with this individual.
            These are accumulated with ``parent.statistic`` and allow
            statistics to accurately represent the population.
        '''
        super(SequenceIndividual, self).__init__(genes, parent, statistic)

class SequenceSpecies(Species):
    '''Provides individuals with fixed-length genomes of integer values.
    Each gene is an integer between zero (inclusive) and ``item_count``
    (exclusive).
    '''
    
    name = 'Sequence'
    
    def __init__(self, cfg, eval_default):
        super(SequenceSpecies, self).__init__(cfg, eval_default)
        # Make some names public within the execution context
        self.public_context = {
            'random_seq': self.init_random,
            'random_sequence': self.init_random,
            'forward_sequence': self.init_forward,
            'reverse_sequence': self.init_reverse,
        }
    
    def legal(self, indiv):
        '''Check to see if an individual is legal.'''
        return len(set(indiv.genome)) == len(indiv.genome)
    
    @classmethod
    def _get_length(cls, length, item_count):
        '''Returns the actual length value based on two parameters.'''
        assert length is not True, "length has no value"
        assert item_count is not True, "item_count has no value"
        if length is None: length = item_count
        
        if hasattr(length, 'get'): length = length.get('exact')
        
        length = int(length)
        assert length > 0, "item_count (length) must be greater than zero"
        
        return length
    
    def init_random(self, length=None, item_count=10, template=None):
        '''Returns instances of `SequenceIndividual` initialised with
        random sequences.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          length : int > 0
            The number of items to include in each individual.
            
            If omitted, the value of `item_count` is used.
          
          item_count : int > 0
            The number of items to include in each individual.
          
          template : `SequenceIndividual` [optional]
            If provided, used to determine the values for `lowest`,
            `highest`, `lower_bounds` and `upper_bounds`.
        '''
        shuffle = rand.shuffle
        genes = list(xrange(self._get_length(length, item_count)))
        
        while True:
            shuffle(genes)
            yield SequenceIndividual(genes, parent=self)
    
    def init_forward(self, length=None, item_count=10):
        '''Returns instances of `SequenceIndividual` initialised in
        ascending order.
        
        Parameters are the same as for `init_random`.
        '''
        genes = list(xrange(self._get_length(length, item_count)))
        
        while True:
            yield SequenceIndividual(genes, parent=self)
    
    def init_reverse(self, length=None, item_count=10):
        '''Returns instances of `SequenceIndividual` initialised in
        descending order.
        
        Parameters are the same as for `init_random`.
        '''
        genes = list(reversed(xrange(self._get_length(length, item_count))))
        
        while True:
            yield SequenceIndividual(genes, parent=self)
    
    def repair(self, _source, randomly=True, sequentially=False):
        '''Repairs a group of individuals by replacing duplicate values.
        
        If `sequentially` is ``False``, repairs are performed by
        replacing a randomly selected duplicate with a randomly selected
        valid value.
        
        If `sequentially` is ``True``, repairs are performed by
        replacing the first duplicate of a value with the lowest
        available value missing from the individual.
        
        :Parameters:
          _source : iterable(`SequenceIndividual`)
            A sequence of individuals. Individuals are taken one at a
            time from this sequence and either returned unaltered or
            cloned and mutated.
          
          randomly : bool
            Specifies random repairs. This is the default behaviour.
          
          sequentially : bool
            Specifies sequential repairs.
        '''
        for indiv in _source:
            has = set(indiv.genome)
            
            if len(has) == len(indiv.genome):
                # No repairs necessary
                yield indiv
                continue
            
            needs = set(xrange(len(indiv.genome)))
            
            new_genes = list(indiv.genome)
            dups = collections.defaultdict(list)
            for i, g in enumerate(indiv.genome):
                dups[g].append(i)
            dups = dict(i for i in dups.iteritems() if len(i[1]) > 1)
            
            if randomly and not sequentially:
                wants = list(needs - has)
                rand.shuffle(wants)
                for locs in dups.itervalues():
                    while len(locs) > 1:
                        i = locs.pop(rand.randrange(len(locs)))
                        new_genes[i] = wants.pop(0)
            else:
                wants = list(sorted(needs - has))
                for i in sorted(chain.from_iterable(islice(i, 1, None) for i in dups.itervalues())):
                    new_genes[i] = wants.pop(0)
            
            yield type(indiv)(genes=new_genes, parent=indiv, statistic={'repaired': 1})
    
    def mutate_random(self, _source, per_indiv_rate=1.0, per_gene_rate=0.1, genes=None):
        '''Mutates a group of individuals by exchanging randomly
        selected genes.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`SequenceIndividual`)
            A sequence of individuals. Individuals are taken one at a
            time from this sequence and either returned unaltered or
            cloned and mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an
            individual is not mutated, it is returned unmodified.
          
          per_gene_rate : |prob|
            The probability of any gene being mutated. If an individual
            is not selected for mutation (under `per_indiv_rate`) then
            this value is unused.
          
          genes : int
            The exact number of genes to mutate. If `None`,
            `per_gene_rate` is used instead.
        '''
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_gene_rate is not True, "per_gene_rate has no value"
        assert genes is not True, "genes has no value"
        
        frand = rand.random
        irand = rand.randrange
        shuffle = rand.shuffle
        
        do_all_gene = (per_gene_rate >= 1.0)
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        genes = int(genes or 0)
        
        for indiv in _source:
            if do_all_indiv or frand() < per_indiv_rate:
                new_genes = list(indiv.genome)
                len_genes = len(new_genes)
                
                if genes:
                    for _ in xrange(genes):
                        i1, i2 = irand(len_genes), irand(len_genes)
                        new_genes[i1], new_genes[i2] = new_genes[i2], new_genes[i1]
                else:
                    for _ in xrange(len_genes):
                        if do_all_gene or frand() < per_gene_rate:
                            i1, i2 = irand(len_genes), irand(len_genes)
                            new_genes[i1], new_genes[i2] = new_genes[i2], new_genes[i1]
                
                yield type(indiv)(new_genes, indiv, statistic={ 'mutated': 1 })
            else:
                yield indiv
    
