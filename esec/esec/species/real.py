'''Provides the `RealSpecies` and `RealIndividual` classes for
real-valued genomes.
'''
from itertools import izip
from itertools import islice
import math
from esec.species import Species
from esec.individual import Individual
from esec.context import rand
import esec.utils as utils

# Disabled: method could be a function
#pylint: disable=R0201

# Override Individual to provide one that keeps its valid bounds with it
class RealIndividual(Individual):
    '''An `Individual` for real-valued genomes. The valid range of each
    gene is stored with the individual so it may be used during mutation
    operations without being respecified.
    '''
    def __init__(self, genes, parent, lower_bounds=None, upper_bounds=None, statistic=None):
        '''Initialises a new `RealIndividual`. Instances are generally
        created using the initialisation methods provided by `RealSpecies`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          genes : iterable(float)
            The sequence of genes that make up the new individual.
          
          parent : `RealIndividual` or `Species`
            Either the `RealIndividual` that was used to generate the
            new individual, or an instance of `RealSpecies`.
            
            If a `RealIndividual` is provided, its values for
            `lower_bounds` and `upper_bounds` are used instead of the
            parameters provided.
          
          lower_bounds : list(float)
            The inclusive lower limit on genome values. Each element
            applies to the gene at the matching index.
            
            These values are used in mutation operations and for value
            validation.
          
          upper_bounds : list(float)
            The exclusive upper limit on genome values. Each element
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
        
        if isinstance(parent, RealIndividual):
            self.lower_bounds = parent.lower_bounds
            self.upper_bounds = parent.upper_bounds
        
        assert isinstance(self.lower_bounds, (list, tuple)), \
            "Lower bounds must be a tuple, not " + str(type(self.lower_bounds))
        assert isinstance(self.upper_bounds, (list, tuple)), \
            "Upper bounds must be a tuple, not " + str(type(self.upper_bounds))
        
        super(RealIndividual, self).__init__(genes, parent, statistic)
    
    @property
    def genome_string(self):
        '''Returns a string representation of the genes of this individual.
        '''
        return '[' + ', '.join(['%g' % g for g in self.genome]) + ']'
    
    @property
    def phenome_string(self):
        '''Returns a string representation of the phenome of this individual.
        '''
        if self._eval and hasattr(self._eval, 'phenome_string'):
            try: return self._eval.phenome_string(self)
            except AttributeError: pass
        return '[' + ', '.join(['%.3f' % p for p in self.phenome]) + ']'

class RealSpecies(Species):
    '''Provides individuals with fixed- or variable-length genomes of
    numeric values. Each gene is a double-precision floating-point value
    between the provided ``lowest`` and ``highest`` values (inclusive).
    '''
    
    name = 'Real'
    
    def __init__(self, cfg, eval_default):
        super(RealSpecies, self).__init__(cfg, eval_default)
        # Make some names public within the execution context
        self.public_context = {
            'random_real': self.init_random,
            'real_low': self.init_low,
            'real_high': self.init_high,
            'real_toggle': self.init_toggle,
        }
    
    def legal(self, indiv):
        '''Check to see if an individual is legal.'''
        for lower, i, upper in izip(indiv.lower_bounds, indiv, indiv.upper_bounds):
            if not (lower <= i <= upper):
                return False
        return True
    
    @classmethod
    def _convert_bounds(cls, src, length):
        '''Produces valid upper/lower bounds lists from the provided input.'''
        if isinstance(src, list): pass
        elif hasattr(src, '__iter__'): src = list(src)
        else: src = [float(src)] * length
        if len(src) < length: src += [src[-1]] * (length - len(src))
        return src
        
    def _init(self, length, shortest, longest, lowest, highest, lower_bounds, upper_bounds, _gen):
        '''Returns instances of `RealIndividual` initialised using the function in
        `_gen`.
        '''
        assert length is not True, "length has no value"
        assert shortest is not True, "shortest has no value"
        assert longest is not True, "longest has no value"
        assert lowest is not True, "lowest has no value"
        assert highest is not True, "highest has no value"
        assert lower_bounds is not True, "lower_bounds has no value"
        assert upper_bounds is not True, "upper_bounds has no value"
        
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
        
        if shortest == longest:
            while True:
                genes = [_gen(*i) for i in izip(lowest, highest, xrange(shortest))]
                yield RealIndividual(genes, parent=self, lower_bounds=lower_bounds, upper_bounds=upper_bounds)
        else:
            irand = rand.randrange
            while True:
                length = irand(shortest, longest+1)
                genes = [_gen(*i) for i in izip(lowest, highest, xrange(length))]
                yield RealIndividual(genes, parent=self, lower_bounds=lower_bounds, upper_bounds=upper_bounds)
    
    def init_random(self,
                    length=None, shortest=10, longest=10,
                    lowest=0.0, highest=1.0,
                    lower_bounds=None, upper_bounds=None,
                    template=None):
        '''Returns instances of `RealIndividual` initialised with random values.
        
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
          
          lowest : float or iterable(float)
            The smallest initialisation value of any particular gene.
            
            If a list of values is provided it must be at least
            `longest` long. Otherwise, the last value in the sequence
            will be used for all subsequent positions.
          
          highest : float |ge| `lowest` or iterable(float)
            The largest initialisation value of any particular gene.
            
            If a list of values is provided it must be at least
            `longest` long. Otherwise, the last value in the sequence
            will be used for all subsequent positions.
          
          lower_bounds : float or iterable(float) [optional]
            The hard inclusive lower limit for each gene (or all genes)
            of the individual.
            
            If unspecified, `lowest` is used as the hard limit.
          
          upper_bounds : float or iterable(float) [optional]
            The hard inclusive upper limit for each gene (or all genes)
            of the individual.
            
            If unspecified, `highest` is used as the hard limit.
          
          template : `RealIndividual` [optional]
            If provided, used to determine the values for `lowest`, 
            `highest`, `lower_bounds` and `upper_bounds`.
        '''
        frand = rand.random
        if template:
            return self._init(length, shortest, longest, template.lower_bounds, template.upper_bounds, None, None,
                              lambda low, high, _: frand() * (high - low) + low)
        else:
            return self._init(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds,
                              lambda low, high, _: frand() * (high - low) + low)
    
    def init_low(self,
                 length=None, shortest=10, longest=10,
                 lowest=0.0, highest=1.0,
                 lower_bounds=None, upper_bounds=None):
        '''Returns instances of `RealIndividual` initialised with `lowest`.
        
        Parameters are the same as for `init_random`.
        '''
        return self._init(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds,
                          lambda low, high, _: low)
    
    def init_high(self,
                  length=None, shortest=10, longest=10,
                  lowest=0.0, highest=1.0,
                  lower_bounds=None, upper_bounds=None):
        '''Returns instances of `RealIndividual` initialised with `highest`.
        
        Parameters are the same as for `init_random`.
        '''
        return self._init(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds,
                          lambda low, high, _: high)
    
    def init_toggle(self,
                    length=None, shortest=10, longest=10,
                    lowest=0.0, highest=1.0,
                    lower_bounds=None, upper_bounds=None):
        '''Returns instances of `RealIndividual`. Every second individual (from
        the first one returned) is initialised with `highest`; the remainder with
        `lowest`.
        
        Parameters are the same as for `init_random`.
        '''
        low_gen = self.init_low(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds)
        high_gen = self.init_high(length, shortest, longest, lowest, highest, lower_bounds, upper_bounds)
        while True:
            yield next(high_gen)
            yield next(low_gen)
    
    def crossover_average(self, _source, per_pair_rate=None, per_indiv_rate=1.0, per_gene_rate=1.0): #pylint: disable=W0613
        '''Performs crossover by averaging the gene values from two individuals
        to create a single offspring.
        
        Returns a sequence of crossed individuals based on the
        individuals in `_source`.
        
        The number of individuals returned is half the number of individuals in
        `_source`, rounded towards zero.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. Individuals are taken two at a
            time from this sequence and recombined to produce one new
            individual.
          
          per_pair_rate : |prob|
            The probability of any particular pair of individuals being
            recombined. If two individuals are not recombined, the first
            is returned unmodified.
            
            If this is ``None``, the value of `per_indiv_rate` is used.
          
          per_indiv_rate : |prob|
            A synonym for `per_pair_rate`.
          
          per_gene_rate : |prob|
            The probability of any particular gene position in a pair
            of individuals being averaged. If averaging does not occur,
            the value from the first individual of the pair is retained.
        '''
        assert per_pair_rate is not True, "per_pair_rate has no value"
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_gene_rate is not True, "per_indiv_rate has no value"
        
        if per_pair_rate is None: per_pair_rate = per_indiv_rate
        if per_pair_rate <= 0.0 or per_gene_rate <= 0.0:
            skip = True
            for indiv in _source:
                if not skip: yield indiv
                skip = not skip
            raise StopIteration
        
        do_all_pairs = (per_pair_rate >= 1.0)
        do_all_genes = (per_gene_rate >= 1.0)
        
        frand = rand.random
        
        for i1, i2 in utils.pairs(_source):
            if do_all_pairs or frand() < per_pair_rate:
                i1_genome, i2_genome = i1.genome, i2.genome
                
                new_genes = list(i1_genome)
                
                if do_all_genes:
                    for i, g2 in enumerate(i2_genome):
                        new_genes[i] = (new_genes[i] + g2) / 2
                else:
                    for i, g2 in enumerate(i2_genome):
                        if frand() < per_gene_rate:
                            new_genes[i] = (new_genes[i] + g2) / 2
                
                i1 = type(i1)(new_genes, i1, statistic={ 'recombined': 1 })
            yield i1
    
    def mutate_random(self, _source, per_indiv_rate=1.0, per_gene_rate=0.1, genes=None):
        '''Mutates a group of individuals by replacing genes with random values.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`RealIndividual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an individual
            is not mutated, it is returned unmodified.
          
          per_gene_rate : |prob|
            The probability of any gene being mutated. If an individual is not
            selected for mutation (under `per_indiv_rate`) then this value is
            unused. If `genes` is specified, this value is ignored.
          
          genes : int
            The exact number of genes to mutate. If `None`, `per_gene_rate` is
            used instead.
        '''
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_gene_rate is not True, "per_gene_rate has no value"
        assert genes is not True, "genes has no value"
        
        frand = rand.random
        shuffle = rand.shuffle
        
        do_all_gene = (per_gene_rate >= 1.0)
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        genes = int(genes or 0)
        
        for indiv in _source:
            assert isinstance(indiv, RealIndividual), "Want RealIndividual, not '%s'" % type(indiv)
            
            if do_all_indiv or frand() < per_indiv_rate:
                new_genes = list(indiv.genome)
                source = izip(xrange(len(new_genes)), indiv.lower_bounds, indiv.upper_bounds)
                source = (i for i in source if not math.isinf(i[1]) and not math.isinf(i[2]))
                
                if genes:
                    do_all_gene = True
                    source = list(source)
                    shuffle(source)
                    source = islice(source, genes)
                
                for i, low, high in source:
                    if do_all_gene or frand() < per_gene_rate:
                        new_genes[i] = frand() * (high - low) + low
                yield type(indiv)(genes=new_genes, parent=indiv, statistic={ 'mutated': 1 })
            else:
                yield indiv
    
    def mutate_delta(self, _source, step_size=0.1, per_indiv_rate=1.0,
                     per_gene_rate=0.1, genes=None,
                     positive_rate=0.5):
        '''Mutates a group of individuals by adding or subtracting `step_size`
        to or from individiual genes.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`RealIndividual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          step_size : float
            The amount to adjust mutated genes by.
          
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
        assert step_size is not True, "step_size has no value"
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_gene_rate is not True, "per_gene_rate has no value"
        assert genes is not True, "genes has no value"
        assert positive_rate is not True, "positive_rate has no value"
        
        frand = rand.random
        shuffle = rand.shuffle
        
        do_all_gene = (per_gene_rate >= 1.0)
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        genes = int(genes or 0)
        
        for indiv in _source:
            assert isinstance(indiv, RealIndividual), "Want `RealIndividual`, not `%s`" % type(indiv)
            
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
                
                yield type(indiv)(genes=new_genes, parent=indiv, statistic={ 'mutated': 1, 'step_sum': step_size_sum })
            else:
                yield indiv
    
    def mutate_gaussian(self, _source, step_size=0.1, sigma=None, per_indiv_rate=1.0, per_gene_rate=0.1, genes=None):
        '''Mutates a group of individuals by adding or subtracting a random
        value with Gaussian distribution based on `step_size` or `sigma`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`RealIndividual`)
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
        assert step_size is not True, "step_size has no value"
        assert sigma is not True, "sigma has no value"
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_gene_rate is not True, "per_gene_rate has no value"
        assert genes is not True, "genes has no value"
        
        sigma = sigma or (step_size * 1.253)
        frand = rand.random
        shuffle = rand.shuffle
        gauss = rand.gauss
        
        do_all_gene = (per_gene_rate >= 1.0)
        do_all_indiv = (per_indiv_rate >= 1.0)
        
        genes = int(genes or 0)
        
        for indiv in _source:
            assert isinstance(indiv, RealIndividual), "Want `RealIndividual`, not `%s`" % type(indiv)
            
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
                        step = gauss(0, sigma)
                        step_size_sum += step
                        new_gene = gene + step
                        new_genes[i] = (low  if new_gene <= low  else
                                        high if new_gene >= high else
                                        new_gene)
                
                yield type(indiv)(genes=new_genes, parent=indiv, statistic={ 'mutated': 1, 'step_sum': step_size_sum })
            else:
                yield indiv
