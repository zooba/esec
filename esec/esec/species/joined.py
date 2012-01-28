'''A species for joined individuals.

Joined individuals do not support standard mutation operations. Standard
recombination operations are available, though should be used with care.

The `JoinedSpecies.crossover_tuple` operation is specifically designed
for joined individuals.
'''

from esec.context import rand
from esec.individual import Individual
from esec.species import Species
from esec.generators import _key_fitness

class JoinedIndividual(Individual):
    '''Represents a set of `Individual` objects which represent one
    solution.
    
    Behaves identically to the `Individual` class with the exception
    that the genome is now a list of the joined individuals (in the
    order provided to the initialiser).
    '''
    
    def __init__(self, members, parent=None):
        '''Initialises a new individual made up of a set of joined
        individuals. Each individual is positioned within the genome of
        the joined individual in the order provided.
        
        :Parameters:
          members : iterable(`Individual`)
            The set of individuals joined to create this individual.
          
          parent : `JoinedIndividual` or `Species`
            Either the `JoinedIndividual` (or derived class) that was
            used to generate the new individual, or the `Species`
            descriptor that defines the type of individual.
            
            If a `JoinedIndividual` is provided, any derived initialiser
            should inherit any specific characteristics (such as size or
            value limits) from the parent.
        '''
        super(JoinedIndividual, self).__init__(members, parent or JoinedSpecies.instance)

    @property
    def genome_string(self):
        '''Returns a string representation of the genes of this individual.
        '''
        return '{[' + '], ['.join([g.genome_string for g in self.genome]) + ']}'
    
    @property
    def phenome_string(self):
        '''Returns a string representation of the phenome of this individual.
        '''
        if self._eval and hasattr(self._eval, 'phenome_string'):
            try: return self._eval.phenome_string(self)
            except AttributeError: pass
        return '{[' + '], ['.join([p.phenome_string for p in self.phenome]) + ']}'


class JoinedSpecies(Species):
    '''Species class for joined individuals. Joined individuals do not
    not generally have a wide range of operations, but automatically
    support any generic recombination operation.
    '''
    
    _include_automatically = False
    
    name = "Joined Individuals"
    
    def __init__(self):
        '''Initialises a default `JoinedSpecies`.'''
        super(JoinedSpecies, self).__init__({ }, None)
        
        # disable length-varying commands
        self.mutate_insert = None
        self.mutate_delete = None
    
    instance = None
    '''A singleton instance of `JoinedSpecies` that should be used when
    creating new instances of `JoinedIndividual`.
    '''

    def best_of_tuple(self, _source):   #pylint: disable=R0201
        '''Returns a sequence of the individuals with highest fitness from
        each `JoinedIndividual` provided.

        :Parameters:
          _source : iterable(`JoinedIndividual`)
            A sequence of joined individuals.
        '''

        for indiv in _source:
            yield max(indiv, key=_key_fitness)
    
    def from_tuple(self, _source, index=1): #pylint: disable=R0201
        '''Returns a sequence of the individuals at the specified index
        in each `JoinedIndividual` provided.

        .. include:: epydoc_include.txt

        :Parameters:
          _source : iterable(`JoinedIndividual`)
            A sequence of joined individuals.

          index : int |ge| 1
            The one-based index into each joined individual.
        '''
        assert index is not True, "index has no value"

        index -= 1
        for indiv in _source:
            yield indiv[index]

    def crossover_tuple(self, _source,  #pylint: disable=R0201
                        per_indiv_rate=1.0,
                        greediness=0.0):
        '''Performs per-gene crossover by selecting one gene from each
        individual in the tuples provided in `_source`.
        
        Returns a sequence of crossed individuals based on the individuals
        in `_source`. The resulting sequence will contain as many
        individuals as `_source`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`JoinedIndividual`)
            A sequence of joined individuals. The `Individual` instances
            making up the joined individual are used to select the new
            genes.
          
          per_indiv_rate : |prob|
            The probability of any particular group of individuals being
            recombined. If individuals are not combined, the first
            individual in the joined individual is returned unmodified.
            If this value is ``None``, the value of `per_pair_rate` is
            used.
          
          greediness : |prob|
            The probability of always selecting a gene from the first
            individual in the joined individual. If the gene is not
            selected, a gene is selected from any one of the individuals
            with equal probability.
        '''
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert greediness is not True, "greediness has no value"
        
        if per_indiv_rate <= 0.0 or greediness >= 1.0:
            for indiv in _source: yield indiv[0]
            raise StopIteration
        
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        frand = rand.random
        
        for indiv in _source:
            if do_all_indiv or frand() < per_indiv_rate:
                new_genes = list(indiv[0].genome)
                len_indiv = len(indiv)
                # Iterate through tuples of the genes at each point in the
                # genomes, filling with None if an individual is shorter
                # than the rest.
                for i in xrange(len(new_genes)):
                    if greediness <= 0.0 or frand() >= greediness:
                        src = None
                        while not src or len(src.genome) <= i:
                            src = indiv[int(frand()*len_indiv)]
                        
                        new_genes[i] = src[i]
                yield type(indiv[0])(new_genes, indiv[0], statistic={ 'recombined': 1 })
            else:
                yield indiv[0]


JoinedSpecies.instance = JoinedSpecies()

