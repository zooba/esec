'''The default set of species types.

A species determines the type and range of gene values contained in
`Individual` instances belonging to it.

:Note:
    Some species provide a derived version of `Individual` and
    include checks to ensure that the derived version is always
    used. Apart from initialisation generators, all operations
    should use ``type(individual)`` when constructing new
    individuals.

.. packagetree:: esec.species
   :style: UML
'''

from esec.utils import merge_cls_dicts, cfg_validate, ConfigDict

class Species(object):
    '''Abstract base class for species descriptors.
    '''
    
    name = 'species'
    
    def __init__(self, cfg, eval_default):
        '''Initialises a new `Species` instance.
        
        :Parameters:
          cfg : dict, `ConfigDict`
            The set of configuration options applying to this
            species. No syntax is provided by the `Species`
            base class, but derived classes may require certain
            parameters.
          
          eval_default : evaluator
            The default evaluator for `Individual` instances of
            this species. Evaluators provide a method `eval`
            taking a single individual as a parameter.
        '''
        # Merge syntax and default details
        self.syntax = merge_cls_dicts(self, 'syntax')
        self.cfg = ConfigDict(merge_cls_dicts(self, 'default'))
        # Now apply user cfg details and test against syntax
        self.cfg.overlay(cfg)
        cfg_validate(self.cfg, self.syntax, type(self), warnings=False)
        # Store default evaluator
        self._eval_default = eval_default
        '''The default evaluator for individuals of this species type.'''
        # Initialise public_context if necessary
        if not hasattr(self, 'public_context'):
            self.public_context = { }
            '''Items to include in a system's execution context. This
            typically contains references to the initialisers provided
            by the species.'''
        
        # Set some default properties to imitiate Individual
        self.species = self
        '''Provided to make `Species` and `Individual` trivially compatible.
        
        :see: Individual.species
        '''
        self._eval = eval_default
        '''Provided to make `Species` and `Individual` trivially compatible.
        
        :see: Individual._eval
        '''
        self.statistic = { }
        '''Provided to make `Species` and `Individual` trivially compatible.
        
        :see: Individual.statistic
        '''
    
    #pylint: disable=R0201
    def mutate_insert(self, _source, per_indiv_rate=0.1, length=None, shortest=1, longest=10, longest_result=20):
        '''Mutates a group of individuals by inserting random gene sequences.
        
        Gene sequences are created by using the ``init_random`` method provided by
        the derived species type. This ``init_random`` method must include a
        parameter named ``template`` which receives an individual to obtain bounds
        and values from.
        
        This method should be overridden for species that don't support random
        insertion directly into the genome.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an individual
            is not mutated, it is returned unmodified.
          
          length : int > 0 [optional]
            The number of genes to insert at each mutation. If left
            unspecified, a random number between `shortest` and `longest`
            (inclusive) is used to determine the length.
          
          shortest : int > 0
            The smallest number of genes that may be inserted at any
            mutation.
          
          longest : int > `shortest`
            The largest number of genes that may be inserted at any
            mutation.
          
          longest_result : int > 0
            The longest new genome that may be created. The length of
            the inserted segment is deliberately selected to avoid
            creating programs longer than this. If there is no way to
            avoid creating a longer genome, the original individual
            is returned and an ``'aborted'`` notification is sent to
            the monitor from ``'mutate_insert'``.
        '''
        if length is not None: shortest = longest = length
        
        shortest = int(shortest)
        longest = int(longest)
        longest_result = int(longest_result)
        
        assert longest >= shortest, \
               "Value of longest (%d) must be higher or equal to shortest (%d)" % (longest, shortest)
        
        frand = rand.random     #pylint: disable=E0602
        irand = rand.randrange  #pylint: disable=E0602
        
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        for indiv in _source:
            if do_all_indiv or frand() < per_indiv_rate:
                len_indiv = len(indiv.genome)
                cut = irand(len_indiv)
                lmax = (longest) if (len_indiv + longest < longest_result) else (longest_result - len_indiv)
                indrand = indiv.init_random(length=longest, template=indiv)
                if lmax >= shortest:
                    insert = next(indrand)[:irand(shortest, lmax+1)]
                    stats = { 'mutated': 1, 'inserted_genes': len(insert) }
                    yield type(indiv)(indiv.genome[:cut] + insert + indiv.genome[cut:], indiv, statistic=stats)
                else:
                    value = {'i': indiv, 'longest_result': longest_result}
                    notify('mutate_insert', 'aborted', value)   #pylint: disable=E0602
                    yield indiv
            else:
                yield indiv
    
    #pylint: disable=R0201
    def mutate_delete(self, _source, per_indiv_rate=0.1, length=None, shortest=1, longest=10, shortest_result=1):
        '''Mutates a group of individuals by deleting random gene sequences.
        
        The number of genes to delete is selected randomly. If this value is the same as
        the number of genes in the individual, all but the first `shortest_result` genes
        are deleted.
        
        This method should be overridden for species that don't support random
        deletion directly from the ``genome`` property.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an individual
            is not mutated, it is returned unmodified.
          
          length : int > 0 [optional]
            The number of genes to delete at each mutation. If left
            unspecified, a random number between `shortest` and `longest`
            (inclusive) is used to determine the length.
          
          shortest : int > 0
            The smallest number of genes that may be deleted at any
            mutation.
          
          longest : int > `shortest`
            The largest number of genes that may be deleted at any
            mutation.
          
          shortest_result : int > 0
            The shortest new genome that may be created. The length
            of the deleted segment is deliberately selected to avoid
            creating programs shorter than this. If the original
            individual is this length or shorter, it is returned
            unmodified.
        '''
        if length is not None: shortest = longest = length
        
        shortest = int(shortest)
        longest = int(longest)
        longest_result = int(longest_result)
        
        assert longest >= shortest, \
               "Value of longest (%d) must be higher or equal to shortest (%d)" % (longest, shortest)
        
        frand = rand.random     #pylint: disable=E0602
        irand = rand.randrange  #pylint: disable=E0602
        
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        for indiv in _source:
            len_indiv = len(indiv.genome)
            if len_indiv > shortest_result and (do_all_indiv or frand() < per_indiv_rate):
                lmax = len_indiv - shortest_result
                if lmax > longest: lmax = longest
                length = irand(shortest, lmax+1) if lmax >= shortest else len_indiv
                if length < len_indiv:
                    cut1 = irand(len_indiv - length)
                    cut2 = cut1 + length
                    stats = { 'mutated': 1, 'deleted_genes': length }
                    yield type(indiv)(indiv.genome[:cut1] + indiv.genome[cut2:], indiv, statistic=stats)
                else:
                    new_indiv = indiv.genome[:shortest_result]
                    deleted = len_indiv - len(new_indiv)
                    if deleted:
                        yield type(indiv)(new_indiv, indiv, statistic={ 'mutated': 1, 'deleted_genes': deleted })
                    else:
                        yield indiv
            else:
                yield indiv

JoinedSpecies = Species({ }, None)      #pylint: disable=C0103
'''Placeholder class for joined individuals. (Joined individuals do
not have a species.)
'''

SPECIES = []
'''An automatically generated list of the available species types.'''

def _do_import():
    '''Automatically populates SPECIES with all the modules in this folder.
    
    :Note:
        Written as a function to prevent local variables from being imported.
    '''
    import os
    
    for _, _, files in os.walk(__path__[0]):
        for filename in (file for file in files if file[0] != '_' and file[-3:] == '.py'):
            modname = filename[:filename.find('.')]
            mod = __import__(modname, globals(), fromlist=[])
            for cls in (getattr(mod, s) for s in dir(mod)):
                if cls is not Species and type(cls) is type and issubclass(cls, Species):
                    SPECIES.append(cls)
                    globals()[cls.__name__] = cls

_do_import()

def include(*species):
    '''Adds `species` to the list of available species types. This
    method is used by plugins to advertise their species.
    
    :Parameters:
      species : `Species` subclass type
        A list of types representing the new species.
    '''
    assert all(type(s) is type for s in species), "species.include() requires a species type (class), not an instance"
    assert all(issubclass(s, Species) for s in species), "New species type must derive from Species class"
    SPECIES.extend(species)
    
