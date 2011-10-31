'''A species for joined individuals.

Joined individuals do not support standard mutation operations. Standard
recombination operations are available, though should be used with care.

The `JoinedSpecies.crossover_tuple` operation is specifically designed
for joined individuals.
'''

import itertools
from esec.context import rand
from esec.individual import Individual
from esec.species import Species

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
    
    def crossover_tuple(self, _source,  #pylint: disable=R0201
                        per_indiv_rate=None, per_pair_rate=1.0,
                        per_gene_rate=None):
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
          
          per_pair_rate : |prob|
            A synonym for `per_indiv_rate`.
          
          per_gene_rate : |prob| [optional]
            The probability of not selecting a gene from the first
            individual in the joined individual. If the gene is not
            selected, a gene is selected from one of the other individuals
            with equal probability.
            If omitted, a gene is selected from any individual with equal
            probability. If set to 1.0 or higher, the first individual in
            each joined individual is returned unmodified.
        '''
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_pair_rate is not True, "per_pair_rate has no value"
        assert per_gene_rate is not True, "per_gene_rate has no value"
        
        if per_indiv_rate is None: per_indiv_rate = per_pair_rate
        if per_indiv_rate <= 0.0 or (per_gene_rate is not None and per_gene_rate >= 1.0):
            for indiv in _source: yield indiv[0]
            raise StopIteration
        
        do_all_indiv = (per_indiv_rate >= 1.0)
        equal_per_gene_rate = (per_gene_rate is None)
        
        frand = rand.random
        
        for indiv in _source:
            if do_all_indiv or frand() < per_indiv_rate:
                new_genes = [ ]
                # Iterate through tuples of the genes at each point in the
                # genomes, filling with None if an individual is shorter
                # than the rest.
                for genes in itertools.izip_longest(*(i.genome for i in indiv)):
                    genes = [i for i in genes if i is not None]
                    len_genes = len(genes)
                    if len_genes == 0: break
                    elif len_genes == 1: new_genes.append(genes[0])
                    elif equal_per_gene_rate: new_genes.append(genes[int(frand()*len_genes)])
                    elif frand() >= per_gene_rate: new_genes.append(genes[0])
                    else: new_genes.append(genes[int(frand()*(len_genes-1)+1)])
                yield type(indiv[0])(new_genes, indiv[0], statistic={ 'recombined': 1 })
            else:
                yield indiv[0]


JoinedSpecies.instance = JoinedSpecies()

