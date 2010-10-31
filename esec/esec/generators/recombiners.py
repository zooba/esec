'''A set of recombinations generators that take multiple individuals and
return a set of new individuals based on groups of the original set.

The global variable ``rand`` and function ``notify`` are imported from
`esec.context` and so are available when the recombiners are executed.

Since some species provide a derived version of `Individual` and include
type validation, all constructors should use ``type`` on an existing
`Individual` to ensure the correct derivation is used.
'''

from itertools import izip as zip   #pylint: disable=W0622
from itertools import islice, chain
from esec.context import rand, notify

def _pairs(source):
    '''Returns pairs of values from `source`.
    
    Equivalent to ``zip(source[::2], source[1::2])`` but doesn't
    require `source` to be a list.'''
    while True:
        yield next(source), next(source)


def Uniform(_source,
            per_pair_rate=None, per_indiv_rate=1.0, per_gene_rate=0.5,
            one_child=False, two_children=None):
    '''Performs uniform crossover by selecting genes at random from
    one of two individuals.
    
    Returns a sequence of crossed individuals based on the individuals
    in `_source`.
    
    If `one_child` is ``True`` (or `two_children` is ``False``), the number
    of individuals returned is half the number of individuals in `_source`,
    rounded towards zero.
    
    If `one_child` is ``False`` (or `two_children` is ``True``), the number
    of individuals returned is the largest even number less than or equal
    to the number of individuals in `_source`.
    
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
      
      one_child : bool
        If ``True``, only one child is returned from each crossover
        operation.
        
        If `two_children` is specified, its value is used instead of this.
      
      two_children : bool
        If ``True``, both children are returned from each crossover
        operation. If ``False``, only one is.
        
        If ``None``, the value of `one_child` is used instead (with the
        opposite meaning to `two_children`).
    '''
    if per_pair_rate is None: per_pair_rate = per_indiv_rate
    if two_children is not None: one_child = not two_children
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
    
    frand = rand.random
    
    for i1, i2 in _pairs(_source):
        if do_all_pairs or frand() < per_pair_rate:
            i1_genome, i2_genome = i1.genome, i2.genome
            i1_len, i2_len = len(i1_genome), len(i2_genome)
            
            new_genes1 = list(i1_genome)
            new_genes2 = list(i2_genome)
            for i in xrange(i1_len if i1_len < i2_len else i2_len):
                if frand() < per_gene_rate:
                    new_genes1[i] = i2_genome[i]
                    new_genes2[i] = i1_genome[i]
            
            i1 = type(i1)(new_genes1, i1, statistic={ 'recombined': 1 })
            i2 = type(i2)(new_genes2, i2, statistic={ 'recombined': 1 })
        
        if one_child:
            yield i1 if frand() < 0.5 else i2
        else:
            yield i1
            yield i2

def Same(_source,
         points=1,
         per_pair_rate=None, per_indiv_rate=1.0,
         one_child=False, two_children=None):
    '''Performs crossover by selecting a `points` points common to both
    individuals and exchanging the sequences of genes to the right
    (including the selection).
    
    Returns a sequence of crossed individuals based on the individuals
    in `_source`.
    
    If `one_child` is ``True`` (or `two_children` is ``False``), the number
    of individuals returned is half the number of individuals in `_source`,
    rounded towards zero.
    
    If `one_child` is ``False`` (or `two_children` is ``True``), the number
    of individuals returned is the largest even number less than or equal
    to the number of individuals in `_source`.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Individuals are taken two at a time
        from this sequence, recombined to produce two new individuals,
        and yielded separately.
      
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
        operation.
        
        If `two_children` is specified, its value is used instead of this.
      
      two_children : bool
        If ``True``, both children are returned from each crossover
        operation. If ``False``, only one is.
        
        If ``None``, the value of `one_child` is used instead (with the
        opposite meaning to `two_children`).
    '''
    if per_pair_rate is None: per_pair_rate = per_indiv_rate
    if two_children is not None: one_child = not two_children
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
                    new_genes1 = list(chain(islice(new_genes1, cut_i), cut2, islice(new_genes1, cut_j, None)))
                    new_genes2 = list(chain(islice(new_genes2, cut_i), cut1, islice(new_genes2, cut_j, None)))
                
                i1 = type(i1)(new_genes1, i1, statistic={ 'recombined': 1 })
                i2 = type(i2)(new_genes2, i2, statistic={ 'recombined': 1 })
        if one_child:
            yield i1 if frand() < 0.5 else i2
        else:
            yield i1
            yield i2

def SingleSame(_source,
               per_pair_rate=None, per_indiv_rate=1.0,
               one_child=False, two_children=None):
    '''A specialisation of `Same` for single-point crossover.'''
    return Same(_source,
                points=1,
                per_pair_rate=per_pair_rate, per_indiv_rate=per_indiv_rate,
                one_child=one_child, two_children=two_children)

def DoubleSame(_source,
               per_pair_rate=None, per_indiv_rate=1.0,
               one_child=False, two_children=None):
    '''A specialisation of `Same` for two-point crossover.'''
    return Same(_source,
                points=2,
                per_pair_rate=per_pair_rate, per_indiv_rate=per_indiv_rate,
                one_child=one_child, two_children=two_children)

def Different(_source,          #pylint: disable=R0915
              points=1,
              per_pair_rate=None, per_indiv_rate=1.0,
              longest_result=None,
              one_child=False, two_children=None):
    '''Performs multi-point crossover by selecting a point in each
    individual and exchanging the sequence of genes to the right
    (including the selection). The selected points are not necessarily
    the same in each individual.
    
    Returns a sequence of crossed individuals based on the individuals
    in `_source`.
    
    If `one_child` is ``True`` (or `two_children` is ``False``), the number
    of individuals returned is half the number of individuals in `_source`,
    rounded towards zero.
    
    If `one_child` is ``False`` (or `two_children` is ``True``), the number
    of individuals returned is the largest even number less than or equal
    to the number of individuals in `_source`.
    
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
      
      longest_result : int [optional]
        The longest new individual to create. The crossover points are
        deliberately selected to avoid creating individuals longer than
        this. If there is no way to avoid creating a longer individual,
        the original individuals are returned and an ``'aborted'``
        notification is sent to the monitor from
        ``'crossover_different'``.
      
      one_child : bool
        If ``True``, only one child is returned from each crossover
        operation.
        
        If `two_children` is specified, its value is used instead of this.
      
      two_children : bool
        If ``True``, both children are returned from each crossover
        operation. If ``False``, only one is.
        
        If ``None``, the value of `one_child` is used instead (with the
        opposite meaning to `two_children`).
    '''
    if per_pair_rate is None: per_pair_rate = per_indiv_rate
    if two_children is not None: one_child = not two_children
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
                
                for (i1_cut_i, i1_cut_j), (i2_cut_i, i2_cut_j) in zip(_pairs(iter(i1_cuts)), _pairs(iter(i2_cuts))):
                    i1_cut = islice(new_genes1, i1_cut_i, i1_cut_j)
                    i2_cut = islice(new_genes2, i2_cut_i, i2_cut_j)
                    new_genes1 = list(chain(islice(new_genes1, i1_cut_i), i2_cut, islice(new_genes1, i1_cut_j, None)))
                    new_genes2 = list(chain(islice(new_genes2, i2_cut_i), i1_cut, islice(new_genes2, i2_cut_j, None)))
                
                i1_len, i2_len = len(new_genes1), len(new_genes2)
                if longest_result and i1_len > longest_result:
                    notify('crossover_different', 'aborted', { 'longest_result': longest_result, 'i1_len': i1_len })
                else:
                    i1 = type(i1)(new_genes1, i1, statistic={ 'recombined': 1 })
                
                if longest_result and i2_len > longest_result:
                    notify('crossover_different', 'aborted', { 'longest_result': longest_result, 'i2_len': i2_len })
                else:
                    i2 = type(i2)(new_genes2, i2, statistic={ 'recombined': 1 })
        
        if one_child:
            yield i1 if frand() < 0.5 else i2
        else:
            yield i1
            yield i2

def SingleDifferent(_source,
                    per_pair_rate=None, per_indiv_rate=1.0,
                    longest_result=None,
                    one_child=False, two_children=None):
    '''A specialisation of `Different` for single-point crossover.'''
    return Different(_source,
                     points=1,
                     per_pair_rate=per_pair_rate, per_indiv_rate=per_indiv_rate,
                     longest_result=longest_result,
                     one_child=one_child, two_children=two_children)

def DoubleDifferent(_source,
                    per_pair_rate=None, per_indiv_rate=1.0,
                    longest_result=None,
                    one_child=False, two_children=None):
    '''A specialisation of `Different` for two-point crossover.'''
    return Different(_source,
                     points=2,
                     per_pair_rate=per_pair_rate, per_indiv_rate=per_indiv_rate,
                     longest_result=longest_result,
                     one_child=one_child, two_children=two_children)


def Segmented(_source,
            per_pair_rate=None, per_indiv_rate=1.0, switch_rate=0.1,
            one_child=False, two_children=None):
    '''Performs segmented crossover by exchanging random segments between
    two individuals. The first segment has `switch_rate` probability of
    being exchanged, while subsequent segments alternate between exchanging
    and non-exchanging.
    
    Returns a sequence of crossed individuals based on the individuals
    in `_source`.
    
    If `one_child` is ``True`` (or `two_children` is ``False``), the number
    of individuals returned is half the number of individuals in `_source`,
    rounded towards zero.
    
    If `one_child` is ``False`` (or `two_children` is ``True``), the number
    of individuals returned is the largest even number less than or equal
    to the number of individuals in `_source`.
    
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
      
      switch_rate : |prob|
        The probability of the current segment ending. Exchanged segments
        are always followed by non-exchanged segments.
        
        This is also the probability of the first segment being exchanged.
        It is reset for each pair of individuals.
      
      one_child : bool
        If ``True``, only one child is returned from each crossover
        operation.
        
        If `two_children` is specified, its value is used instead of this.
      
      two_children : bool
        If ``True``, both children are returned from each crossover
        operation. If ``False``, only one is.
        
        If ``None``, the value of `one_child` is used instead (with the
        opposite meaning to `two_children`).
    '''
    if per_pair_rate is None: per_pair_rate = per_indiv_rate
    if two_children is not None: one_child = not two_children
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


def PerGeneTuple(_source, per_indiv_rate=None, per_pair_rate=1.0, per_gene_rate=None):
    '''Performs per-gene crossover by selecting one gene from each
    individual in the tuples provided in `_source`.
    
    Returns a sequence of crossed individuals based on the individuals
    in `_source`. The resulting sequence will contain as many individuals
    as `_source`.
    
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
    if per_indiv_rate is None: per_indiv_rate = per_pair_rate
    if per_indiv_rate <= 0.0 or per_gene_rate >= 1.0:
        for indiv in _source: yield indiv[0]
        raise StopIteration
    
    do_all_indiv = (per_indiv_rate >= 1.0)
    equal_per_gene_rate = (per_gene_rate is None)
    
    frand = rand.random
    choice = rand.choice
    
    for indiv in _source:
        if do_all_indiv or frand() < per_indiv_rate:
            new_genes = [ ]
            # Iterate through tuples of the genes at each point in the
            # genomes, filling with None if an individual is shorter than
            # the rest.
            for genes in map(lambda *args: args, *(i.genome for i in indiv)):
                genes = [i for i in genes if i is not None]
                len_genes = len(genes)
                if len_genes == 0: break
                elif len_genes == 1: new_genes.append(genes[0])
                elif equal_per_gene_rate: new_genes.append(choice(genes))
                elif frand() >= per_gene_rate: new_genes.append(genes[0])
                else: new_genes.append(choice(genes[1:]))
            yield type(indiv[0])(new_genes, indiv[0], statistic={ 'recombined': 1 })
        else:
            yield indiv[0]
