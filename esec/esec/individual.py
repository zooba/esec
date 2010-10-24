'''The representation of single entities for use in system groups. Each
`Individual` contains an immutable set of gene values. The values of each
gene are determined by the `Species` to which the individual belongs.

Every `Individual` exposes both a ``genome`` value and a ``phenome`` value.
Indexing directly into an `Individual` (or using ``len()``) uses the phenome.
By default, most phenomes are identical to the genome.
Operations that modify individuals use the genome value while evaluations use
(often implicitly) the phenome value. The separation is used to transparently
provide binary to real and integer values mappings.

The ``genome_string`` and ``phenome_string`` properties on each `Individual`
return human-readable versions of the genome and phenome, respectively.

For the purpose of evolutionary search, each `Individual` or some combination
of individuals (see `JoinedIndividual`) represents a potential solution to a
problem.

'''

from esec.fitness import Fitness, EmptyFitness
from esec.context import notify
from itertools import izip as zip   #pylint: disable=W0622
import itertools

class Individual(object):
    '''Represents a single member of the population with some type
    of internal genome.
    '''
    
    # _birthday is a private class variable used for assigning birthdates
    # to instances.
    _birthday = 0
    '''The most recently provided birth date. This value is global
    across all individuals deriving from `Individual`.'''
    
    @classmethod
    def reset_birthday(cls):
        '''Resets the next birthday value.
        '''
        cls._birthday = 0
    
    @classmethod
    def _next_birthday(cls):
        '''Returns the next birthday value. Also notifies the monitor
        with the notification ``'statistic'`` and value ``'births'``.
        '''
        cls._birthday += 1
        notify('individual', 'statistic', 'births')
        return cls._birthday
    
    def __init__(self, genes, parent, statistic=None):
        '''Initialises a new individual.
        
        :Parameters:
          genes : iterable
            The sequence of genes that make up the new individual.
          
          parent : `Individual` or `Species`
            Either the `Individual` (or derived class) that was used
            to generate the new individual, or the `Species` descriptor
            that defines the type of individual.
            
            If an `Individual` is provided, any derived initialiser
            should inherit any specific characteristics (such as size
            or value limits) from the parent.
          
          statistic : dict [optional]
            A set of statistic values associated with this individual.
            These are accumulated with ``parent.statistic`` and allow
            statistics to accurately represent the population.
        '''
        assert genes, "Genes must be provided"
        assert parent, "Parent must be provided"
        self._fitness = EmptyFitness()
        '''The fitness of this individual. `EmptyFitness` indicates that a
        fitness evaluation is required, after which it is replaced by an
        instance of `Fitness`.'''
        self.birthday = None
        '''The birthday value for this individual.'''
        self.genome = list(genes)
        '''The gene values for this individual. Gene values are considered
        immutable.'''
        self.statistic = statistic or { }
        '''The statistics specifically associated with this individual.'''
        
        # Species classes provide default values for species, _eval and statistic
        # so we can save testing for them
        assert hasattr(parent, 'species'), "Parent object must provide 'species' member"
        assert hasattr(parent, '_eval'), "Parent object must provide '_eval' member"
        assert hasattr(parent, 'statistic'), "Parent object must provide 'statistic' member"
        self.species = parent.species
        '''The species type of this individual.'''
        # We are allowed to read parent._eval
        #pylint: disable=W0212
        self._eval = parent._eval
        '''The current evaluator for this individual. ``EVAL`` statements
        in the system definition change this member.
        '''
        
        for key, value in parent.statistic.iteritems():
            if key in self.statistic:
                self.statistic[key] += value
            else:
                self.statistic[key] = value
    
    def born(self):
        '''Sets the individual's birthday to the next available value. If
        ``self.birthday`` is already set, it is left unchanged.
        
        :Returns: `self`
        '''
        if self.birthday == None:
            self.birthday = Individual._next_birthday()
        return self
    
    def __getattr__(self, name):
        '''Attempts to locate unknown members on the species descriptor associated
        with this individual.
        
        If `name` is not found on either `self` or ``self.species``, an AttributeError
        is raised. (This matches the standard behaviour for an unknown attribute.)
        '''
        # Handle and re-raise AttributeError to ensure it comes from Individual and not the species
        attr = getattr(self.species, name, None)
        if not attr: raise AttributeError("'%s' object has no attribute '%s'" % (type(self).__name__, name))
        else: return attr
    
    @property
    def fitness(self):
        '''Gets or sets the fitness of this individual. If the fitness has not
        been determined, it is calculated using the current evaluator for this
        individual and cached.
        
        Deleting ``self.fitness`` or setting it to ``None`` uninitialises the
        value.
        '''
        if not isinstance(self._fitness, Fitness):
            # use `notify` rather than `statistic` to ensure that all evals are counted.
            # `statistic` is intended for counting events that only matter if they remain
            # in the population.
            if not self._eval: self._eval = self._eval_default
            _fit = self._eval.eval(self)
            if isinstance(_fit, Fitness): self._fitness = _fit
            elif _fit != None: self._fitness = Fitness(_fit)
            else: self._fitness = EmptyFitness()
            notify('individual', 'statistic', 'local_evals+global_evals')
        return self._fitness
    
    # Pylint doesn't understand @x.setter and @x.deleter
    #pylint: disable=E1101,E0102,C0111
    
    @fitness.setter
    def fitness(self, value):
        if isinstance(value, Fitness):
            self._fitness = value
        elif value == None:
            self._fitness = EmptyFitness()
        else:
            self._fitness = Fitness(value)
    
    @fitness.deleter
    def fitness(self):
        self._fitness = EmptyFitness()
    
    def __len__(self):
        '''Returns the number of values in the phenome.
        '''
        return len(self.phenome)
    
    def __getitem__(self, key):
        '''Returns the phenome value located at `key`.
        '''
        return self.phenome.__getitem__(key)
    
    def __iter__(self):
        '''Returns an iterator over the phenome values of this individual.
        '''
        return self.phenome.__iter__()
    
    def __str__(self):
        '''
        :Returns:
            A string representation including the name of the species, the
            birthday and the fitness of this individual.
        
        :Note:
            If `fitness` has not previously been read, calling this method
            may trigger a fitness evaluation.
        '''
        return '[%s: born=%d fitness=%s]' % (self.species.name, self.birthday, self.fitness)
    
    @property
    def phenome(self):
        '''Returns the phenome of this individual.
        
        By default, this matches the genome.
        '''
        return self.genome
    
    @property
    def genome_string(self):
        '''Returns a string representation of the genes of this individual.
        '''
        return str(self.genome)
    
    @property
    def phenome_string(self):
        '''Returns a string representation of the phenome of this individual.
        '''
        return self.genome_string
    
    @property
    def length_string(self):
        '''Returns a string representation of the length of this individual.
        '''
        return str(len(self))



class JoinedIndividual(Individual):
    '''Represents a set of `Individual` objects which represent one solution.
    
    Behaves identically to the `Individual` class with the exception that
    the genome is now a list of the joined individuals (in the order
    provided to the initialiser) and individuals may be retrived by the
    name of the group they were obtained from.
    '''
    
    def __init__(self, members, sources, parent=None):
        '''Initialises a new individual made up of a set of joined
        individuals. Each individual can be obtained by the name of the
        group it came from. If multiple individuals come from the same
        group, only the first one provided in `members` is accessible
        by name.
        
        :Parameters:
          members : iterable(`Individual`)
            The set of individuals joined to create this individual.
          
          sources : iterable(string)
            The names of the group the individuals in `members` were
            obtained from.
          
          parent : `JoinedIndividual` or `Species`
            Either the `JoinedIndividual` (or derived class) that was
            used to generate the new individual, or the
            `Species` descriptor that defines the type of individual.
            
            If a `JoinedIndividual` is provided, any derived initialiser
            should inherit any specific characteristics (such as size
            or value limits) from the parent.
        '''
        if not parent:
            from esec.species import JoinedSpecies
            parent = JoinedSpecies
        super(JoinedIndividual, self).__init__(members, parent)
        self.sources = { }
        for source, member in zip(sources, self.genome):
            if source not in self.sources:
                self.sources[source] = member
    
    def __contains__(self, key):
        if isinstance(key, str):
            return key in self.sources
        else:
            return super(JoinedIndividual, self).__contains__(key)
    
    def __getitem__(self, key):
        if isinstance(key, str) and key in self.sources:
            return self.sources[key]
        else:
            return super(JoinedIndividual, self).__getitem__(key)

# EmptyIndividual and OnIndividual have no public methods
#pylint: disable=R0903
class EmptyIndividual(object):
    '''Represents a non-existent Individual. Used for initialisation.
    '''
    
    def __init__(self):
        self.fitness = EmptyFitness()
        self.birthday = -1
        self.genome = [ ]
        self.species = None
    
    def __len__(self):
        return 0
    
    def __iter__(self):
        return self.genome.__iter__()
    
    def __str__(self):
        return '[Empty: born=%d fitness=---]' % self.birthday
    
    @property
    def phenome(self):  #pylint: disable=R0201
        '''Returns the phenome of this individual.
        '''
        return self.genome
    
    @property
    def genome_string(self):  #pylint: disable=R0201
        '''Returns a string representation of the genes of this individual.
        '''
        return '-'
    
    @property
    def phenome_string(self): #pylint: disable=R0201
        '''Returns a string representation of the phenome of this individual.
        '''
        return '-'
    
    @property
    def length_string(self):    #pylint: disable=R0201
        '''Returns a string representation of the length of this individual.
        '''
        return '0'

class OnIndividual(object):
    '''Dynamically binds a call to the individual on which it will operate.
    
    The call is resolved by using ``getattr`` on the first individual in the
    group.
    '''
    def __init__(self, target, default=None):
        '''Initialises a new `OnIndividual`.
        
        :Parameters:
          target : str
            The name of the target method.
          
          default : function
            The function to call if `target` is not found. If
            `default` is ``None`` and `target` is not found,
            an assertion will be raised.
        '''
        self.target = target
        self.default = default
    
    def __call__(self, _source, *params, **named):
        '''Calls ``self.target`` on the first individual in `_source`, passing
        all of `_source` as a parameter along with any other parameters.
        '''
        first = next(_source)
        target = getattr(first, self.target, self.default)
        assert target, "Method %s does not exist on %s" % (self.target , type(first))
        return target(_source=itertools.chain((first,), _source), *params, **named)
    
    def __repr__(self):
        if self.default:
            return '<function %s on Individual or %s>' % (self.target, self.default)
        else:
            return '<function %s on Individual>' % self.target
