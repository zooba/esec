'''Provides the `IntegerSpecies` and `IntegerIndividual` classes for
integer-valued genomes.
'''
from itertools import izip
from itertools import islice
from esec.species import Species
from esec.individual import Individual
from esec.context import rand

# Disabled: method could be a function
#pylint: disable=R0201

# Override Individual to provide one that keeps its valid bounds with it
class IntegerIndividual(Individual):
    '''An `Individual` for integer-valued genomes. The valid range of each
    gene is stored with the individual so it may be used during mutation
    operations without being respecified.
    '''
    def __init__(self, genes, parent, lower_bounds=None, upper_bounds=None, statistic=None):
        '''Initialises a new `IntegerIndividual`. Instances are generally
        created using the initialisation methods provided by
        `IntegerSpecies`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          genes : iterable(int)
            The sequence of genes that make up the new individual.
          
          parent : `IntegerIndividual` or `Species`
            Either the `IntegerIndividual` that was used to generate the
            new individual, or an instance of `IntegerSpecies`.
            
            If an `IntegerIndividual` is provided, its values for
            `lower_bounds` and `upper_bounds` are used instead of the
            parameters provided.
          
          lower_bounds : list(int)
            The inclusive lower limit on genome values. Each element
            applies to the gene at the matching index.
            
            These values are used in mutation operations and for value
            validation.
          
          upper_bounds : list(int)
            The inclusive upper limit on genome values. Each element
            applies to the gene at the matching index.
            
            These values are used in mutation operations and for value
            validation.
          
          statistic : dict [optional]
            A set of statistic values associated with this individual.
            These are accumulated with ``parent.statistic`` and allow
            statistics to accurately represent the population.
        '''
        self.lower_bounds = lower_bounds
        self.upper_bounds = upper_bounds
        
        if isinstance(parent, IntegerIndividual):
            self.lower_bounds = parent.lower_bounds
            self.upper_bounds = parent.upper_bounds
        
        assert isinstance(self.lower_bounds, (list, tuple)), \
            "Lower bounds must be a tuple, not " + str(type(self.lower_bounds))
        assert isinstance(self.upper_bounds, (list, tuple)), \
            "Upper bounds must be a tuple, not " + str(type(self.upper_bounds))
        
        super(IntegerIndividual, self).__init__(genes, parent, statistic)

class IntegerSpecies(Species):
    '''Provides individuals with fixed- or variable-length genomes of
    integer values. Each gene is an integer between the provided
    ``lowest`` and ``highest`` values (inclusive).
    '''
    
    name = 'Integer'
    
    def __init__(self, cfg, eval_default):
        super(IntegerSpecies, self).__init__(cfg, eval_default)
        # Make some names public within the execution context
        self.public_context = {
            'random_int': self.init_random,
            'random_integer': self.init_random,
            'integer_low': self.init_low,
            'integer_high': self.init_high,
            'integer_toggle': self.init_toggle,
            'integer_increment': self.init_increment,
            'integer_count': self.init_count,
        }
    
    @classmethod
    def _convert_bounds(cls, src, length):
        '''Produces valid upper/lower bounds lists from the provided input.'''
        if isinstance(src, list): pass
        elif hasattr(src, '__iter__'): src = list(src)
        else: src = [int(src)] * length
        if len(src) < length: src += [src[-1]] * (length - len(src))
        return src
        
    def _init(self, length, shortest, longest, lowest, highest, lower_bounds, upper_bounds, _gen):
        '''Returns instances of `IntegerIndividual` initialised using the function
        in `_gen`.
        '''
        if hasattr(length, 'get'):
            shortest = length.get('min', 0)
            longest = length.get('max', 0)
            length = length.get('exact', 0)
        
        if length: shortest = longest = length
        
        shortest = int(shortest)
        longest = int(longest)
        
        assert shortest > 0, "Shortest must be greater than zero"
        assert longest >= shortest, \
            "Value of longest (%d) must be higher or equal to shortest (%d)" % (longest, shortest)
        
        if not lower_bounds: lower_bounds = lowest
        if not upper_bounds: upper_bounds = highest
        
        lowest = self._convert_bounds(lowest, longest)
        highest = self._convert_bounds(highest, longest)
        lower_bounds = self._convert_bounds(lower_bounds, longest)
        upper_bounds = self._convert_bounds(upper_bounds, longest)
        
        assert all(h >= l for h, l in izip(highest, lowest)), \
            "Values of highest (%s) must be greater than or equal to those in lowest (%s)" % (highest, lowest)
        
        if shortest >= longest:
            while True:
                genes = [_gen(*i) for i in izip(lowest, highest, xrange(shortest))]
                yield IntegerIndividual(genes, parent=self, lower_bounds=lower_bounds, upper_bounds=upper_bounds)
        else:
            irand = rand.randrange
            while True:
                length = irand(shortest, longest+1)
                genes = [_gen(*i) for i in izip(lowest, highest, xrange(length))]
                yield IntegerIndividual(genes, parent=self, lower_bounds=lower_bounds, upper_bounds=upper_bounds)

    def init_random(self,
                    length=None, shortest=10, longest=10,
                    lowest=0, highest=255,
                    lower_bounds=None, upper_bounds=None,
                    template=None):
        '''Returns instances of `IntegerIndividual` initialised with random values.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          length : int > 0 or dictionary
            The number of genes to include in each individual. If left
            unspecified, a random number between `shortest` and
            `longest` (inclusive) is used to determine the length of
            each individual.
            
            If a dictionary is passed, the ``'min'``, ``'max'`` and
            ``'exact'`` members are used as values for `shortest`,
            `longest` and `length`, respectively. This simplifies
            passing the dimensions of a landscape.
          
          shortest : int > 0
            The smallest number of genes in any individual.
          
          longest : int > `shortest`
            The largest number of genes in any individual.
          
          lowest : int or iterable(int)
            The smallest initialisation value of any particular gene.
            
            If a list of values is provided it must be at least
            `longest` long. Otherwise, the last value in the sequence
            will be used for all subsequent positions.
          
          highest : int |ge| `lowest` or iterable(int)
            The largest initialisation value of any particular gene.
            
            If a list of values is provided it must be at least
            `longest` long. Otherwise, the last value in the sequence
            will be used for all subsequent positions.
          
          lower_bounds : int or iterable(int) [optional]
            The hard inclusive lower limit for each gene (or all genes)
            of the individual.
            
            If unspecified, `lowest` is used as the hard limit.
          
          upper_bounds : int or iterable(int) [optional]
            The hard inclusive upper limit for each gene (or all genes)
            of the individual.
            
            If unspecified, `highest` is used as the hard limit.
          
          template : `IntegerIndividual` [optional]
            If provided, used to determine the values for `lowest`,
            `highest`, `lower_bounds` and `upper_bounds`.
        '''
        irand = rand.randrange
        if template:
            return self._init(length, shortest, longest, template.lower_bounds, template.upper_bounds, None, None,
                              lambda low, high, _: irand(low, high + 1))
        else:
            return self._init(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds,
                              lambda low, high, _: irand(low, high + 1))
    
    def init_low(self,
                 length=None, shortest=10, longest=10,
                 lowest=0, highest=255,
                 lower_bounds=None, upper_bounds=None):
        '''Returns instances of `IntegerIndividual` initialised with `lowest`.
        
        Parameters are the same as for `init_random`.
        '''
        return self._init(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds,
                          lambda low, high, _: low)
    
    def init_high(self,
                  length=None, shortest=10, longest=10,
                  lowest=0, highest=255,
                  lower_bounds=None, upper_bounds=None):
        '''Returns instances of `IntegerIndividual` initialised with `highest`.
        
        Parameters are the same as for `init_random`.
        '''
        return self._init(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds,
                          lambda low, high, _: high)
    
    def init_toggle(self,
                    length=None, shortest=10, longest=10,
                    lowest=0, highest=255,
                    lower_bounds=None, upper_bounds=None):
        '''Returns instances of `IntegerIndividual`. Every second individual (from
        the first one returned) is initialised with `highest`; the remainder with
        `lowest`.
        
        Parameters are the same as for `init_random`.
        '''
        low_gen = self.init_low(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds)
        high_gen = self.init_high(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds)
        while True:
            yield next(high_gen)
            yield next(low_gen)
    
    def init_increment(self,
                       length=None, shortest=10, longest=10,
                       lowest=0, highest=255,
                       lower_bounds=None, upper_bounds=None):
        '''Returns instances of `IntegerIndividual` initialised with values
        incrementing from `lowest` to `highest` across the genome. If
        `highest` is reached before the end of the genome, counting restarts
        at `lowest`.
        
        Parameters are the same as for `init_random`.
        '''
        return self._init(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds,
                          lambda low, high, i: i % (high - low) + low)
    
    def init_count(self,
                   length=None, shortest=10, longest=10,
                   lowest=0, highest=255,
                   lower_bounds=None, upper_bounds=None):
        '''Returns instances of `IntegerIndividual` initialised with each value
        from `lowest` to `highest`. Each genome contains only a single value.
        When `highest` is reached, counting restarts at `lowest`.
        
        Parameters are the same as for `init_random`.
        '''
        lowest = int(lowest)
        highest = int(highest)
        low_gen = self.init_low(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds)
        count = 0
        while True:
            indiv = next(low_gen)
            indiv.genome[:] = [count % (highest - lowest) + lowest for _ in indiv.genome]
            count += 1
            yield indiv
    
    def mutate_random(self, _source, per_indiv_rate=1.0, per_gene_rate=0.1, genes=None):
        '''Mutates a group of individuals by replacing genes with random values.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`IntegerIndividual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an individual
            is not mutated, it is returned unmodified.
          
          per_gene_rate : |prob|
            The probability of any gene being mutated. If an individual is not
            selected for mutation (under `per_indiv_rate`) then this value is
            unused.
          
          genes : int
            The exact number of genes to mutate. If `None`, `per_gene_rate` is
            used instead.
        '''
        frand = rand.random
        irand = rand.randrange
        shuffle = rand.shuffle
        
        do_all_gene = (per_gene_rate >= 1.0)
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        genes = int(genes or 0)
        
        for indiv in _source:
            if do_all_indiv or frand() < per_indiv_rate:
                new_genes = list(indiv.genome)
                source = izip(xrange(len(new_genes)), indiv.lower_bounds, indiv.upper_bounds)
                
                if genes:
                    do_all_gene = True
                    source = list(source)
                    shuffle(source)
                    source = islice(source, genes)
                
                for i, low, high in source:
                    if do_all_gene or frand() < per_gene_rate:
                        new_genes[i] = irand(low, high + 1)
                
                yield type(indiv)(new_genes, indiv, statistic={ 'mutated': 1 })
            else:
                yield indiv
    
    def mutate_delta(self, _source, step_size=1, per_indiv_rate=1.0, per_gene_rate=0.1, genes=None, positive_rate=0.5):
        '''Mutates a group of individuals by adding or subtracting `step_size`
        to or from individiual genes.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`IntegerIndividual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          step_size : int
            The amount to adjust mutated genes by. If this value is not an
            integer, it is truncated before use.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an individual
            is not mutated, it is returned unmodified.
          
          per_gene_rate : |prob|
            The probability of any gene being mutated. If an individual is not
            selected for mutation (under `per_indiv_rate`) then this value is
            unused.
          
          genes : int
            The exact number of genes to mutate. If `None`, `per_gene_rate` is
            used instead.
          
          positive_rate : |prob|
            The probability of `step_size` being added to the gene value.
            Otherwise, `step_size` is subtracted.
        '''
        frand = rand.random
        shuffle = rand.shuffle
        
        do_all_gene = (per_gene_rate >= 1.0)
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        genes = int(genes or 0)
        
        # Die (if debugging) if step_size is not an integer
        assert step_size == int(step_size), "step_size must be an integer for integer species"
        # Force step_size to be an integer
        step_size = int(step_size)
        
        for indiv in _source:
            assert isinstance(indiv, IntegerIndividual), "Want `IntegerIndividual`, not `%s`" % type(indiv)
            
            if do_all_indiv or frand() < per_indiv_rate:
                step_size_sum = 0
                new_genes = list(indiv.genome)
                source = izip(xrange(len(new_genes)), new_genes, indiv.lower_bounds, indiv.upper_bounds)
                
                if genes:
                    do_all_gene = True
                    source = list(source)
                    shuffle(source)
                    source = islice(source, genes)
                
                for i, gene, low, high in source:
                    if do_all_gene or frand() < per_gene_rate:
                        step_size_sum += step_size
                        new_gene = gene + (step_size if frand() < positive_rate else -step_size)
                        new_genes[i] = (low  if new_gene < low  else
                                        high if new_gene > high else
                                        new_gene)
                
                yield type(indiv)(new_genes, indiv, statistic={ 'mutated': 1, 'step_sum': step_size_sum })
            else:
                yield indiv
    
    def mutate_gaussian(self, _source, step_size=1.0, sigma=None, per_indiv_rate=1.0, per_gene_rate=0.1, genes=None):
        '''Mutates a group of individuals by adding or subtracting a random
        value with Gaussian distribution based on `step_size` or `sigma`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`IntegerIndividual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          step_size : float
            Determines the standard deviation of the distribution used to
            determine the adjustment amount. If `sigma` is provided, this
            value is ignored.
          
          sigma : float
            The standard deviation of the distribution used determine the
            adjust amount. If omitted, the value of `step_size` is used
            to calculate a value for `sigma`.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an individual
            is not mutated, it is returned unmodified.
          
          per_gene_rate : |prob|
            The probability of any gene being mutated. If an individual is not
            selected for mutation (under `per_indiv_rate`) then this value is
            unused.
          
          genes : int
            The exact number of genes to mutate. If `None`, `per_gene_rate` is
            used instead.
        '''
        sigma = sigma or (step_size * 1.253)
        frand = rand.random
        shuffle = rand.shuffle
        gauss = rand.gauss
        
        do_all_gene = (per_gene_rate >= 1.0)
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        genes = int(genes or 0)
        
        for indiv in _source:
            assert isinstance(indiv, IntegerIndividual), "Want `IntegerIndividual`, not `%s`" % type(indiv)
            
            if do_all_indiv or frand() < per_indiv_rate:
                step_size_sum = 0
                new_genes = list(indiv.genome)
                source = izip(xrange(len(new_genes)), new_genes, indiv.lower_bounds, indiv.upper_bounds)
                
                if genes:
                    do_all_gene = True
                    source = list(source)
                    shuffle(source)
                    source = islice(source, genes)
                
                for i, gene, low, high in source:
                    if do_all_gene or frand() < per_gene_rate:
                        step = int(gauss(0, sigma))
                        step_size_sum += step
                        new_gene = gene + step
                        new_genes[i] = (low  if new_gene < low  else
                                        high if new_gene > high else
                                        new_gene)
                
                yield type(indiv)(new_genes, indiv, statistic={ 'mutated': 1, 'step_sum': step_size_sum })
            else:
                yield indiv
