'''A set of recombinations generators that take multiple individuals and
return a set of new individuals based on groups of the original set.

The global variable ``rand`` and function ``notify`` are made available
through the context in which the recombiners are executed.

Since some species provide a derived version of `Individual` and include
type validation, all constructors should use ``type`` on an existing
`Individual` to ensure the correct derivation is used.
'''

def OnePointSame(src, per_pair_rate=None, per_indiv_rate=1.0):
    '''Performs single-point crossover by selecting a single point
    common to both individuals and exchanging the sequence of genes
    to the right (including the selection).
    
    Returns a sequence of crossed individuals based on the individuals
    in `src`. The resulting sequence will contain as many individuals
    as `src` (unless `src` contains an odd number, in which case one
    less will be returned).
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      src : iterable(`Individual`)
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
    '''
    if per_pair_rate == None: per_pair_rate = per_indiv_rate
    if per_pair_rate <= 0.0:
        for indiv in src: yield indiv
        raise StopIteration
    
    do_all_pairs = (per_pair_rate >= 1.0)
    
    frand = rand.random     #pylint: disable=E0602
    irand = rand.randrange  #pylint: disable=E0602
    group = list(src)
    
    for i1_pre, i2_pre in zip(group[::2], group[1::2]):
        if do_all_pairs or frand() < per_pair_rate:
            genome1, genome2 = i1_pre.genome, i2_pre.genome
            len1, len2 = len(genome1), len(genome2)
            
            if len1 <= 1 or len2 <= 1:
                i1_post, i2_post = i1_pre, i2_pre
            else:
                cut = irand(1, min(len1, len2))
                i1_post = type(i1_pre)(genome1[:cut] + genome2[cut:], i1_pre, statistic={ 'recombined': 1 })
                i2_post = type(i2_pre)(genome2[:cut] + genome1[cut:], i2_pre, statistic={ 'recombined': 1 })
            yield i1_post
            yield i2_post
        else:
            yield i1_pre
            yield i2_pre

def OnePointDifferent(src, per_pair_rate=None, per_indiv_rate=1.0, longest_result=None):
    '''Performs single-point crossover by selecting a point in each
    individual and exchanging the sequence of genes to the right
    (including the selection). The selected points are not necessarily
    the same in each individual.
    
    Returns a sequence of crossed individuals based on the individuals
    in `src`. The resulting sequence will contain as many individuals
    as `src` (unless `src` contains an odd number, in which case one
    less will be returned).
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      src : iterable(`Individual`)
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
        The longest new program to create. The crossover points are
        deliberately selected to avoid creating programs longer than
        this. If there is no way to avoid creating a longer program,
        the original individuals are returned and an ``'aborted'``
        notification is sent to the monitor from
        ``'crossover_one_different'``.
    '''
    if per_pair_rate == None: per_pair_rate = per_indiv_rate
    if per_pair_rate <= 0.0:
        for indiv in src: yield indiv
        raise StopIteration
    
    do_all_pairs = (per_pair_rate >= 1.0)
    
    frand = rand.random     #pylint: disable=E0602
    irand = rand.randrange  #pylint: disable=E0602
    group = list(src)
    
    for i1_pre, i2_pre in zip(group[::2], group[1::2]):
        if do_all_pairs or frand() < per_pair_rate:
            genome1, genome2 = i1_pre.genome, i2_pre.genome
            len1, len2 = len(genome1), len(genome2)
            
            if len1 <= 1 and len2 <= 1:
                i1_post, i2_post = i1_pre, i2_pre
            else:
                # determine a random cut point
                cut1 = irand(1, len1) if len1 > 1 else 1
                
                if longest_result:
                    # determine limits to ensure valid size when crossed
                    cut2_low = max(cut1 + len2 - longest_result, 0) + 1
                    cut2_high = min(cut1 - len1 + longest_result, len2)
                    
                    if cut2_low < cut2_high:
                        cut2 = irand(cut2_low, cut2_high)
                    else:
                        cut2 = None
                else:
                    cut2 = irand(1, len2) if len2 > 1 else 1
                
                if cut2:
                    i1_post = type(i1_pre)(genome1[:cut1] + genome2[cut2:], i1_pre, statistic={ 'recombined': 1 })
                    i2_post = type(i2_pre)(genome2[:cut2] + genome1[cut1:], i2_pre, statistic={ 'recombined': 1 })
                else:
                    
                    notify('crossover_one_different', 'aborted',    #pylint: disable=E0602
                           {'i1': i1_pre, 'i2': i2_pre, 'longest_result': longest_result})
                    i1_post, i2_post = i1_pre, i2_pre
            yield i1_post
            yield i2_post
        else:
            yield i1_pre
            yield i2_pre

def PerGeneTuple(src, per_indiv_rate=None, per_pair_rate=1.0, per_gene_rate=None):
    '''Performs per-gene crossover by selecting one gene from each
    individual in the tuples provided in `src`.
    
    Returns a sequence of crossed individuals based on the individuals
    in `src`. The resulting sequence will contain as many individuals
    as `src`.
    
    .. include:: epydoc_include.txt
    
    :Parameters:
      src : iterable(`JoinedIndividual`)
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
        The probability of selecting a gene from the first individual
        in the joined individual. If the gene is not selected, a gene
        is selected from one of the other individuals with equal
        probability.
        If omitted, a gene is selected from any individual with equal
        probability. If set to 1.0 or higher, the first individual in
        each joined individual is returned unmodified.
    '''
    if per_indiv_rate == None: per_indiv_rate = per_pair_rate
    if per_indiv_rate <= 0.0 or per_gene_rate >= 1.0:
        for indiv in src: yield indiv[0]
        raise StopIteration
    
    do_all_indiv = (per_indiv_rate >= 1.0)
    equal_per_gene_rate = (per_gene_rate == None)
    
    frand = rand.random     #pylint: disable=E0602
    choice = rand.choice    #pylint: disable=E0602
    
    for indiv in src:
        if do_all_indiv or frand() < per_indiv_rate:
            new_genes = [ ]
            # Iterate through tuples of the genes at each point in the
            # genomes, filling with None if an individual is shorter than
            # the rest.
            for genes in map(lambda *args: args, *(i.genome for i in indiv)):
                genes = [i for i in genes if i != None]
                len_genes = len(genes)
                if len_genes == 0: break
                elif len_genes == 1: new_genes.append(genes[0])
                elif equal_per_gene_rate: new_genes.append(choice(genes))
                elif frand() < per_gene_rate: new_genes.append(genes[0])
                else: new_genes.append(choice(genes[1:]))
            yield type(indiv[0])(new_genes, indiv[0], statistic={ 'recombined': 1 })
        else:
            yield indiv[0]
