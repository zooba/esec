'''The default set of species types.

A species determines the type and range of gene values contained in
`Individual` instances belonging to it.

:Note:
    Some species provide a derived version of `Individual` and include
    checks to ensure that the derived version is always used. Apart from
    initialisation generators, all operations should use
    ``type(parent)`` when constructing new individuals.

.. packagetree:: esec.species
   :style: UML
'''

from itertools import chain, islice, izip
from esec.context import notify, rand
from esec.utils import merge_cls_dicts, cfg_validate, ConfigDict

def _pairs(source):
    '''Returns pairs of values from `source`.
    
    Equivalent to ``zip(source[::2], source[1::2])`` but doesn't
    require `source` to be a list.
    '''
    while True:
        yield next(source), next(source)

class Species(object):
    '''Abstract base class for species descriptors.
    '''
    
    _include_automatically = True
    '''Indicates whether the class should be included in the set of
    available species. If ``True``, the species is instantiated for
    every system and the contents of `public_context` is merged into the
    system context.
    
    This only applies to classes deriving from `Species` *and* included
    in `esec.species`. Other species classes are never included
    automatically.
    '''
    
    name = 'N/A'
    '''The display name of the species class.
    '''
    
    def __init__(self, cfg, eval_default):
        '''Initialises a new `Species` instance.
        
        :Parameters:
          cfg : dict, `ConfigDict`
            The set of configuration options applying to this species.
            No syntax is provided by the `Species` base class, but
            derived classes may require certain parameters.
          
          eval_default : evaluator
            The default evaluator for `Individual` instances of this
            species. Evaluators provide a method `eval` taking a single
            individual as a parameter.
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
        '''Provided to make `Species` and `Individual` trivially
        compatible.
        
        :see: Individual.species
        '''
        self._eval = eval_default
        '''Provided to make `Species` and `Individual` trivially
        compatible.
        
        :see: Individual._eval
        '''
        self.statistic = { }
        '''Provided to make `Species` and `Individual` trivially
        compatible.
        
        :see: Individual.statistic
        '''
    
    def legal(self, indiv): #pylint: disable=W0613,R0201
        '''Determines whether the specified individual is legal.
        
        By default, this function always returns ``True``. Subclasses
        may override this to perform range or bounds checking or other
        verification appropriate to the species.
        
        :See: esec.individual.Individual.legal
        '''
        return True
    
    #pylint: disable=R0201
    def mutate_insert(self, _source,
                      per_indiv_rate=0.1,
                      length=None, shortest=1, longest=10,
                      longest_result=20):
        '''Mutates a group of individuals by inserting random gene
        sequences.
        
        Gene sequences are created by using the ``init_random`` method
        provided by the derived species type. This ``init_random``
        method must include a parameter named ``template`` which
        receives an individual to obtain bounds and values from.
        
        This method should be overridden for species that don't support
        random insertion directly into the genome.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. Individuals are taken one at a
            time from this sequence and either returned unaltered or
            cloned and mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an
            individual is not mutated, it is returned unmodified.
          
          length : int > 0 [optional]
            The number of genes to insert at each mutation. If left
            unspecified, a random number between `shortest` and
            `longest` (inclusive) is used to determine the length.
          
          shortest : int > 0
            The smallest number of genes that may be inserted at any
            mutation.
          
          longest : int > `shortest`
            The largest number of genes that may be inserted at any
            mutation.
          
          longest_result : int > 0
            The longest new genome that may be created. The length of
            the inserted segment is deliberately selected to avoid
            creating genomes longer than this. If there is no way to
            avoid creating a longer genome, the original individual
            is returned and an ``'aborted'`` notification is sent to
            the monitor from ``'mutate_insert'``.
        '''
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert length is not True, "length has no value"
        assert shortest is not True, "shortest has no value"
        assert longest is not True, "longest has no value"
        assert longest_result is not True, "longest_result has no value"
        
        if length is not None: shortest = longest = length
        
        shortest = int(shortest)
        longest = int(longest)
        longest_result = int(longest_result)
        
        assert longest >= shortest, \
               "Value of longest (%d) must be higher or equal to shortest (%d)" % (longest, shortest)
        
        frand = rand.random
        irand = rand.randrange
        
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
                    value = { 'i': indiv, 'longest_result': longest_result }
                    notify('mutate_insert', 'aborted', value)
                    yield indiv
            else:
                yield indiv
    
    #pylint: disable=R0201
    def mutate_delete(self, _source,
                      per_indiv_rate=0.1,
                      length=None, shortest=1, longest=10,
                      shortest_result=1):
        '''Mutates a group of individuals by deleting random gene
        sequences.
        
        The number of genes to delete is selected randomly. If this
        value is the same as the number of genes in the individual, all
        but the first `shortest_result` genes are deleted.
        
        This method should be overridden for species that don't support
        random deletion directly from the ``genome`` property.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. Individuals are taken one at a
            time from this sequence and either returned unaltered or
            cloned and mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an
            individual is not mutated, it is returned unmodified.
          
          length : int > 0 [optional]
            The number of genes to delete at each mutation. If left
            unspecified, a random number between `shortest` and
            `longest` (inclusive) is used to determine the length.
          
          shortest : int > 0
            The smallest number of genes that may be deleted at any
            mutation.
          
          longest : int > `shortest`
            The largest number of genes that may be deleted at any
            mutation.
          
          shortest_result : int > 0
            The shortest new genome that may be created. The length
            of the deleted segment is deliberately selected to avoid
            creating genomes shorter than this. If the original
            individual is this length or shorter, it is returned
            unmodified.
        '''
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert length is not True, "length has no value"
        assert shortest is not True, "shortest has no value"
        assert longest is not True, "longest has no value"
        assert shortest_result is not True, "shortest_result has no value"
        
        if length is not None: shortest = longest = length
        
        shortest = int(shortest)
        longest = int(longest)
        shortest_result = int(shortest_result)
        
        assert longest >= shortest, \
               "Value of longest (%d) must be higher or equal to shortest (%d)" % (longest, shortest)
        
        frand = rand.random
        irand = rand.randrange
        
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
    
    def crossover_uniform(self, _source,
                          per_pair_rate=None, per_indiv_rate=1.0, per_gene_rate=0.5,
                          discrete=False,
                          one_child=False, two_children=False): #pylint: disable=W0613
        '''Performs uniform crossover by selecting genes at random from
        one of two individuals.
        
        Returns a sequence of crossed individuals based on the individuals
        in `_source`.
        
        If `one_child` is ``True`` the number of individuals returned is
        half the number of individuals in `_source`, rounded towards
        zero. Otherwise, the number of individuals returned is the
        largest even number less than or equal to the number of
        individuals in `_source`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. Individuals are taken two at a time
            from this sequence, recombined to produce two new individuals,
            and yielded separately.
          
          per_pair_rate : |prob|
            The probability of any particular pair of individuals being
            recombined. If two individuals are not recombined, they are
            returned unmodified. If this is ``None``, the value of
            `per_indiv_rate` is used.
          
          per_indiv_rate : |prob|
            A synonym for `per_pair_rate`.
          
          per_gene_rate : |prob|
            The probability of any particular pair of genes being swapped.
          
          discrete : bool
            If ``True``, uses discrete recombination, where source genes
            may be copied rather than exchanged, resulting in the same
            value appearing in both offspring.
          
          one_child : bool
            If ``True``, only one child is returned from each crossover
            operation. `two_children` is the default.
          
          two_children : bool
            If ``True``, both children are returned from each crossover
            operation. If ``False``, only one is. If neither `one_child`
            nor `two_children` are specified, `two_children` is the
            default.
        '''
        assert per_pair_rate is not True, "per_pair_rate has no value"
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_gene_rate is not True, "per_gene_rate has no value"
        
        if per_pair_rate is None: per_pair_rate = per_indiv_rate
        if per_pair_rate <= 0.0 or per_gene_rate <= 0.0:
            if one_child:
                skip = True
                for indiv in _source:
                    if not skip: yield indiv
                    skip = not skip
            else:
                for indiv in _source:
                    yield indiv
            raise StopIteration
        
        do_all_pairs = (per_pair_rate >= 1.0)
        do_all_genes = (per_gene_rate >= 1.0)
        
        frand = rand.random
        
        for i1, i2 in _pairs(_source):
            if do_all_pairs or frand() < per_pair_rate:
                i1_genome, i2_genome = i1.genome, i2.genome
                i1_len, i2_len = len(i1_genome), len(i2_genome)
                
                new_genes1 = list(i1_genome)
                new_genes2 = list(i2_genome)
                for i in xrange(i1_len if i1_len < i2_len else i2_len):
                    if do_all_genes or frand() < per_gene_rate:
                        if discrete:
                            new_genes1[i] = i1_genome[i] if frand() < 0.5 else i2_genome[i]
                            new_genes2[i] = i1_genome[i] if frand() < 0.5 else i2_genome[i]
                        else:
                            new_genes1[i] = i2_genome[i]
                            new_genes2[i] = i1_genome[i]
                
                i1 = type(i1)(new_genes1, i1, statistic={ 'recombined': 1 })
                i2 = type(i2)(new_genes2, i2, statistic={ 'recombined': 1 })
            
            if one_child:
                yield i1 if frand() < 0.5 else i2
            else:
                yield i1
                yield i2

    def crossover_discrete(self, _source,
                           per_pair_rate=None, per_indiv_rate=1.0, per_gene_rate=1.0,
                           one_child=False, two_children=False):
        '''A specialisation of `crossover_uniform` for discrete
        crossover.
        
        Note that `crossover_discrete` has a different default value for
        `per_gene_rate` to `crossover_uniform`.
        '''
        return self.crossover_uniform(
            _source=_source,
            per_pair_rate=per_pair_rate, per_indiv_rate=per_indiv_rate,
            per_gene_rate=per_gene_rate,
            discrete=True,
            one_child=one_child, two_children=two_children)
    
    def crossover(self, _source,
                  points=1,
                  per_pair_rate=None, per_indiv_rate=1.0,
                  one_child=False, two_children=False): #pylint: disable=W0613
        '''Performs crossover by selecting a `points` points common to
        both individuals and exchanging the sequences of genes to the
        right (including the selection).
        
        Returns a sequence of crossed individuals based on the
        individuals in `_source`.
        
        If `one_child` is ``True`` the number of individuals returned is
        half the number of individuals in `_source`, rounded towards
        zero. Otherwise, the number of individuals returned is the
        largest even number less than or equal to the number of
        individuals in `_source`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. Individuals are taken two at a
            time from this sequence, recombined to produce two new
            individuals, and yielded separately.
          
          points : int |ge| 1
            The number of points to cross at. If zero, individuals are
            returned unmodified (respecting the setting of
            `one_child`/`two_children`). If greater than the length of
            the individual, every gene will be exchanged.
          
          per_pair_rate : |prob|
            The probability of any particular pair of individuals being
            recombined. If two individuals are not recombined, they are
            returned unmodified. If this is ``None``, the value of
            `per_indiv_rate` is used.
          
          per_indiv_rate : |prob|
            A synonym for `per_pair_rate`.
          
          one_child : bool
            If ``True``, only one child is returned from each crossover
            operation. `two_children` is the default.
          
          two_children : bool
            If ``True``, both children are returned from each crossover
            operation. If ``False``, only one is. If neither `one_child`
            nor `two_children` are specified, `two_children` is the
            default.
        '''
        assert points is not True, "points has no value"
        assert per_pair_rate is not True, "per_pair_rate has no value"
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        
        if per_pair_rate is None: per_pair_rate = per_indiv_rate
        if per_pair_rate <= 0.0 or points < 1:
            if one_child:
                skip = True
                for indiv in _source:
                    if not skip: yield indiv
                    skip = not skip
            else:
                for indiv in _source:
                    yield indiv
            raise StopIteration
        
        do_all_pairs = (per_pair_rate >= 1.0)
        points = int(points)
        
        frand = rand.random
        shuffle = rand.shuffle
        
        for i1, i2 in _pairs(_source):
            if do_all_pairs or frand() < per_pair_rate:
                i1_genome, i2_genome = i1.genome, i2.genome
                i1_len, i2_len = len(i1_genome), len(i2_genome)
                
                if i1_len > points and i2_len > points:
                    max_len = i1_len if i1_len < i2_len else i2_len
                    cuts = list(xrange(1, max_len))
                    shuffle(cuts)
                    cuts = list(sorted(islice(cuts, points)))
                    cuts.append(max_len)
                    
                    new_genes1 = list(i1_genome)
                    new_genes2 = list(i2_genome)
                    
                    for cut_i, cut_j in _pairs(iter(cuts)):
                        cut1 = islice(new_genes1, cut_i, cut_j)
                        cut2 = islice(new_genes2, cut_i, cut_j)
                        new_genes1 = list(chain(islice(new_genes1, cut_i),
                                                cut2,
                                                islice(new_genes1, cut_j, None)))
                        new_genes2 = list(chain(islice(new_genes2, cut_i),
                                                cut1,
                                                islice(new_genes2, cut_j, None)))
                    
                    i1 = type(i1)(new_genes1, i1, statistic={ 'recombined': 1 })
                    i2 = type(i2)(new_genes2, i2, statistic={ 'recombined': 1 })
            if one_child:
                yield i1 if frand() < 0.5 else i2
            else:
                yield i1
                yield i2
    
    def crossover_one(self, _source,
                      per_pair_rate=None, per_indiv_rate=1.0,
                      one_child=False, two_children=False):
        '''A specialisation of `crossover` for single-point crossover.
        '''
        return self.crossover(
            _source,
            points=1,
            per_pair_rate=per_pair_rate, per_indiv_rate=per_indiv_rate,
            one_child=one_child, two_children=two_children)
    
    def crossover_two(self, _source,
                      per_pair_rate=None, per_indiv_rate=1.0,
                      one_child=False, two_children=False):
        '''A specialisation of `crossover` for two-point crossover.'''
        return self.crossover(
            _source,
            points=2,
            per_pair_rate=per_pair_rate, per_indiv_rate=per_indiv_rate,
            one_child=one_child, two_children=two_children)
    
    def crossover_different(self, _source,  #pylint: disable=R0915
                            points=1,
                            per_pair_rate=None, per_indiv_rate=1.0,
                            longest_result=None,
                            one_child=False, two_children=False):   #pylint: disable=W0613
        '''Performs multi-point crossover by selecting a point in each
        individual and exchanging the sequence of genes to the right
        (including the selection). The selected points are not
        necessarily the same in each individual.
        
        Returns a sequence of crossed individuals based on the
        individuals in `_source`.
        
        If `one_child` is ``True`` the number of individuals returned is
        half the number of individuals in `_source`, rounded towards
        zero. Otherwise, the number of individuals returned is the
        largest even number less than or equal to the number of
        individuals in `_source`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. Individuals are taken two at a
            time from this sequence, recombined to produce two new
            individuals, and yielded separately.
          
          per_pair_rate : |prob|
            The probability of any particular pair of individuals being
            recombined. If two individuals are not recombined, they are
            returned unmodified. If this is ``None``, the value of
            `per_indiv_rate` is used.
          
          per_indiv_rate : |prob|
            A synonym for `per_pair_rate`.
          
          longest_result : int [optional]
            The longest new individual to create. The crossover points
            are deliberately selected to avoid creating individuals
            longer than this. If there is no way to avoid creating a
            longer individual, the original individuals are returned and
            an ``'aborted'`` notification is sent to the monitor from
            ``'crossover_different'``.
          
          one_child : bool
            If ``True``, only one child is returned from each crossover
            operation. `two_children` is the default.
          
          two_children : bool
            If ``True``, both children are returned from each crossover
            operation. If ``False``, only one is. If neither `one_child`
            nor `two_children` are specified, `two_children` is the
            default.
        '''
        assert per_pair_rate is not True, "per_pair_rate has no value"
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert longest_result is not True, "longest_result has no value"
        
        if per_pair_rate is None: per_pair_rate = per_indiv_rate
        if per_pair_rate <= 0.0 or points < 1:
            if one_child:
                skip = True
                for indiv in _source:
                    if not skip: yield indiv
                    skip = not skip
            else:
                for indiv in _source:
                    yield indiv
            raise StopIteration
        
        do_all_pairs = (per_pair_rate >= 1.0)
        points = int(points)
        longest_result = int(longest_result or 0)
        
        frand = rand.random
        shuffle = rand.shuffle
        
        for i1, i2 in _pairs(_source):
            if do_all_pairs or frand() < per_pair_rate:
                i1_genome, i2_genome = i1.genome, i2.genome
                i1_len, i2_len = len(i1_genome), len(i2_genome)
                
                if i1_len > points and i2_len > points:
                    i1_cuts = list(xrange(1, i1_len))
                    i2_cuts = list(xrange(1, i2_len))
                    shuffle(i1_cuts)
                    shuffle(i2_cuts)
                    i1_cuts = list(sorted(islice(i1_cuts, points)))
                    i2_cuts = list(sorted(islice(i2_cuts, points)))
                    i1_cuts.append(i1_len)
                    i2_cuts.append(i2_len)
                    
                    new_genes1 = list(i1_genome)
                    new_genes2 = list(i2_genome)
                    
                    for (i1_cut_i, i1_cut_j), (i2_cut_i, i2_cut_j) in \
                        izip(_pairs(iter(i1_cuts)), _pairs(iter(i2_cuts))):
                        
                        i1_cut = islice(new_genes1, i1_cut_i, i1_cut_j)
                        i2_cut = islice(new_genes2, i2_cut_i, i2_cut_j)
                        new_genes1 = list(chain(islice(new_genes1, i1_cut_i),
                                                i2_cut,
                                                islice(new_genes1, i1_cut_j, None)))
                        new_genes2 = list(chain(islice(new_genes2, i2_cut_i),
                                                i1_cut,
                                                islice(new_genes2, i2_cut_j, None)))
                    
                    i1_len, i2_len = len(new_genes1), len(new_genes2)
                    if longest_result and i1_len > longest_result:
                        notify('crossover_different', 'aborted',
                               { 'longest_result': longest_result, 'i1_len': i1_len })
                    else:
                        i1 = type(i1)(new_genes1, i1, statistic={ 'recombined': 1 })
                    
                    if longest_result and i2_len > longest_result:
                        notify('crossover_different', 'aborted',
                               { 'longest_result': longest_result, 'i2_len': i2_len })
                    else:
                        i2 = type(i2)(new_genes2, i2, statistic={ 'recombined': 1 })
            
            if one_child:
                yield i1 if frand() < 0.5 else i2
            else:
                yield i1
                yield i2
    
    def crossover_one_different(self, _source,
                                per_pair_rate=None, per_indiv_rate=1.0,
                                longest_result=None,
                                one_child=False, two_children=False):
        '''A specialisation of `crossover_different` for single-point
        crossover.
        '''
        return self.crossover_different(
            _source,
            points=1,
            per_pair_rate=per_pair_rate, per_indiv_rate=per_indiv_rate,
            longest_result=longest_result,
            one_child=one_child, two_children=two_children)
    
    def crossover_two_different(self, _source,
                                per_pair_rate=None, per_indiv_rate=1.0,
                                longest_result=None,
                                one_child=False, two_children=False):
        '''A specialisation of `crossover_different` for two-point
        crossover.
        '''
        return self.crossover_different(
            _source,
            points=2,
            per_pair_rate=per_pair_rate, per_indiv_rate=per_indiv_rate,
            longest_result=longest_result,
            one_child=one_child, two_children=two_children)
    
    def crossover_segmented(self, _source,
                            per_pair_rate=None, per_indiv_rate=1.0, switch_rate=0.1,
                            one_child=False, two_children=False):   #pylint: disable=W0613
        '''Performs segmented crossover by exchanging random segments
        between two individuals. The first segment has `switch_rate`
        probability of being exchanged, while subsequent segments
        alternate between exchanging and non-exchanging.
        
        Returns a sequence of crossed individuals based on the
        individuals in `_source`.
        
        If `one_child` is ``True`` the number of individuals returned is
        half the number of individuals in `_source`, rounded towards
        zero. Otherwise, the number of individuals returned is the
        largest even number less than or equal to the number of
        individuals in `_source`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. Individuals are taken two at a
            time from this sequence, recombined to produce two new
            individuals, and yielded separately.
          
          per_pair_rate : |prob|
            The probability of any particular pair of individuals being
            recombined. If two individuals are not recombined, they are
            returned unmodified. If this is ``None``, the value of
            `per_indiv_rate` is used.
          
          per_indiv_rate : |prob|
            A synonym for `per_pair_rate`.
          
          switch_rate : |prob|
            The probability of the current segment ending. Exchanged
            segments are always followed by non-exchanged segments.
            
            This is also the probability of the first segment being
            exchanged. It is reset for each pair of individuals.
          
          one_child : bool
            If ``True``, only one child is returned from each crossover
            operation. `two_children` is the default.
          
          two_children : bool
            If ``True``, both children are returned from each crossover
            operation. If ``False``, only one is. If neither `one_child`
            nor `two_children` are specified, `two_children` is the
            default.
        '''
        assert per_pair_rate is not True, "per_pair_rate has no value"
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert switch_rate is not True, "switch_rate has no value"
        
        if per_pair_rate is None: per_pair_rate = per_indiv_rate
        if per_pair_rate <= 0.0 or not (0.0 < switch_rate < 1.0):
            if one_child:
                skip = True
                for indiv in _source:
                    if not skip: yield indiv
                    skip = not skip
            else:
                for indiv in _source:
                    yield indiv
            raise StopIteration
        
        do_all_pairs = (per_pair_rate >= 1.0)
        
        frand = rand.random
        
        for i1, i2 in _pairs(_source):
            if do_all_pairs or frand() < per_pair_rate:
                i1_genome, i2_genome = i1.genome, i2.genome
                i1_len, i2_len = len(i1_genome), len(i2_genome)
                
                new_genes1 = list(i1_genome)
                new_genes2 = list(i2_genome)
                exchanging = (frand() < switch_rate)
                
                for i in xrange(i1_len if i1_len < i2_len else i2_len):
                    if exchanging:
                        new_genes1[i] = i2_genome[i]
                        new_genes2[i] = i1_genome[i]
                    if frand() < switch_rate:
                        exchanging = not exchanging
                
                i1 = type(i1)(new_genes1, i1, statistic={ 'recombined': 1 })
                i2 = type(i2)(new_genes2, i2, statistic={ 'recombined': 1 })
            
            if one_child:
                yield i1 if frand() < 0.5 else i2
            else:
                yield i1
                yield i2

SPECIES = []
'''An automatically generated list of the available species types.'''

def _do_import():
    '''Automatically populates SPECIES with all the modules in this
    folder.
    
    :Note:
        Written as a function to prevent local variables from being
        imported.
    '''
    import os
    
    for _, _, files in os.walk(__path__[0]):
        for filename in (file for file in files if file[0] != '_' and file[-3:] == '.py'):
            modname = filename[:filename.find('.')]
            mod = __import__(modname, globals(), fromlist=[])
            for cls in (getattr(mod, s) for s in dir(mod)):
                if cls is not Species and type(cls) is type and issubclass(cls, Species):
                    if getattr(cls, '_include_automatically', True):
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
    assert all(type(s) is type for s in species), \
           "species.include() requires a species type (class), not an instance"
    assert all(issubclass(s, Species) for s in species), \
           "New species type must derive from Species class"
    SPECIES.extend(species)
