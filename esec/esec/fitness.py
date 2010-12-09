'''Represent a multi-stage fitness value.

The fitness is multi-stage since sort order is determined
lexicographically, that is, the first element is compared first with the
remaining elements only being used if the first compare equal.

Customisable comparison operations allow "equal" to be redefined
arbitrarily in a way most suitable for that particular value.

The `Fitness` class provides a simple implementation for a single
floating point value where larger values indicate a better fitness.
Derivations of `Fitness` need only override `Fitness.types`,
`Fitness.defaults`, `Fitness.check` and `Fitness.__str__`. Derivations
that don't use lexicographical ordering and value maximisation should
also override `Fitness.__ge__` and potentially `Fitness.__eq__`.

The `EmptyFitness` class provides an efficient sentinel value indicating
that no fitness value has been set. All comparisons return greater-than
and addition and subtraction operations behave as expected against a
matching `Fitness` instance containing all zeros. `EmptyFitness` is
required for use internally, since non-matching derivations of `Fitness`
will raise assertions if used in an operation.
'''

import sys
from types import GeneratorType as generator
from itertools import izip

class Fitness(object):
    '''Represents a multi-stage fitness value.
    
    Each stage has an approach direction and equality tolerance.
    
    Two `Fitness` objects may be compared for (approximate) equality or
    sorted according to their values.
    
    `Fitness` objects may be accumulated and divided for the purpose of
    generating statistics.
    
    Derived classes should replace the `types` and `defaults` variables
    with values suitable for their purposes.
    
    The `__str__` method may be overridden to provide formatted output.
    '''
    
    types = [float]
    '''A list of the types of each part of the fitness value.
    
    Each element specifies one part of the fitness. The matching element
    in `defaults` specifies the default value.
    
    For example::
      
      types    = [float, int ]
      defaults = [  0.0, 100 ]
    
    specifies a fitness value with two parts: the first represented
    as a real number and the second as an integer. The default
    contents of `values` is ``(0.0, 100)``.
    '''
    
    defaults = [0.0]
    '''A list of the defaults of each part of the fitness value.
    
    Each element specifies one part of the fitness. The matching element
    in `types` specifies the type of this part.
    
    For example::
      
      types    = [float, int ]
      defaults = [  0.0, 100 ]
    
    specifies a fitness value with two parts: the first represented
    as a real number and the second as an integer. The default
    contents of `values` is ``(0.0, 100)``.
    '''
    
    def __init__(self, values=None, _direct=False):
        '''Initialises the fitness object with a set of values.
        
        If direct is True, the value in v is assigned directly without
        validation or cloning (for internal use only).
        '''
        
        self.values = None
        '''The set of values defining the `Fitness` object. These
        values should only be set using the constructor or the overriden
        operators. Except for the augmented arithmetic operators,
        `values` should be treated as immutable.
        '''
        
        if _direct:
            self.values = values
        elif values is None:
            self.values = tuple(self.check(i, *args) for i, args in
                                enumerate(izip(self.types, self.defaults, self.defaults)))
        elif isinstance(values, Fitness):
            if __debug__:
                self.values = None
                self.validate(values)
            self.values = tuple(self.check(i, *args) for i, args in
                                enumerate(izip(self.types, self.defaults, values.values)))
        elif isinstance(values, (list, tuple, generator)):
            self.values = tuple(self.check(i, *args) for i, args in
                                enumerate(izip(self.types, self.defaults, values)))
        elif len(self.types) == 1:
            self.values = (self.check(0, self.types[0], self.defaults[0], values),)
        else:
            raise ValueError('Unexpected value %s' % values)
        assert not isinstance(self.values, generator)
        assert len(self.values) == len(self.types), 'Invalid number of values'
    
    def __str__(self):
        if __debug__: self.validate()
        return '%.3f' % self.values[0]
    
    @property
    def simple(self):
        '''Returns the most significant part of the fitness value. This
        value should always be larger (more positive) for a more-fit
        fitness.
        '''
        return self.values[0]
    
    @property
    def comma_separated(self):
        '''Returns the parts of the fitness value separated by commas.
        '''
        return ','.join((str(v) for v in self.values))
    
    def validate(self, other=None):
        '''Verifies that each part of the fitness value matches the type
        specified in `types`. If provided, `other` is also verified.
        
        :Note:
            This method is used internally and is not used at all when
            ``__debug__`` is ``False``.
        '''
        if self.values is not None:
            if not all((isinstance(*args) for args in izip(self.values, self.types))):
                print >> sys.stderr, self.types
                print >> sys.stderr, self.values
                assert False, "Incorrect value type in Fitness object"
        if isinstance(other, EmptyFitness): return
        if other is not None:
            assert isinstance(other, Fitness), "Not comparing to a Fitness object"
            assert self.types == other.types, "Part types do not match between Fitness objects"
            other.validate()
    
    def __gt__(self, other):
        '''Determines whether `self` is more fit than `other`.
        
        A `Fitness` instance is always more fit than ``None`` or any
        object which is not a `Fitness`.
        
        :Parameters:
          other : `Fitness`, ``None`` or another object
            The object to compare this `Fitness` instance to.
        
        :Returns:
            ``True`` if `self` is more fit than `other`; otherwise,
            ``False``.
        
        :Note:
            Derivations should override this method and `__eq__`. All
            other comparison results are based on these methods.
        '''
        if not isinstance(other, Fitness): return True
        # By default, Python performs a lexicographical comparison on sequences.
        return self.values > other.values
    
    def __eq__(self, other):
        '''Determines whether `self` is of equal fitness to `other`.
        
        A `Fitness` instance is never equally fit to ``None`` or any
        object which is not a `Fitness`.
        
        :Parameters:
          other : `Fitness`, ``None`` or another object
            The object to compare this `Fitness` instance to.
        
        :Returns:
            ``True`` if `self` is equally fit to `other`; otherwise,
            ``False``.
        
        :Note:
            Derivations should override this method and `__gt__`. All
            other comparison results are based on these methods.
        '''
        if not isinstance(other, Fitness): return False
        return self.values == other.values
    
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __lt__(self, other):
        return not self.__eq__(other) and not self.__gt__(other)
    
    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)
    
    def __le__(self, other):
        return not self.__gt__(other)
    
    def __hash__(self):
        result = 0
        for i in self.values:
            result ^= hash(i)
        return result
    
    def check(self, index, expected_type, default, value):
        '''Validates each value as it is assigned to a `Fitness` value.

        Unless overriden, this validation only applies at
        initialisation. Arithmetic operations do not validate, otherwise
        bound limits may prevent `Fitness` instances from being used to
        calculate sums and averages.

        To force value validation after arithmetic operations,
        initialise a new `Fitness` instance from the result.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          index : 0 |le| int < len(`types`)
            The index of the relevent element of `types` and `defaults`.
          
          expected_type : type
            The relevant element of `types`.
          
          default
            The relevant element of `defaults`.
          
          value
            The value being assigned to the specified part.
        
        :Returns:
            The validated, and potentially converted, value.
        
        :Note:
            This method casts values to the type specified in `types`.
            For more complex behaviour, such as range validation, this
            method must be overridden in a derived class.
        '''
        # Disable unused parameter and could-be-function messages
        #pylint: disable=W0613,R0201
        return expected_type(value)
    
    def __add__(self, other):
        if __debug__: self.validate(other)
        if isinstance(other, EmptyFitness): return NotImplemented
        values = tuple((value1 + value2 for value1, value2 in izip(self.values, other.values)))
        return type(self)(values, True)
    
    def __neg__(self):
        if __debug__: self.validate()
        return type(self)(tuple(-value for value in self.values), True)
    
    def __sub__(self, other):
        if __debug__: self.validate(other)
        if isinstance(other, EmptyFitness): return NotImplemented
        values = tuple((value1 - value2 for value1, value2 in izip(self.values, other.values)))
        return type(self)(values, True)
    
    def __iadd__(self, other):
        if __debug__: self.validate(other)
        if isinstance(other, EmptyFitness): return NotImplemented
        self.values = tuple((value1 + value2 for value1, value2 in izip(self.values, other.values)))
        return self
    
    def __isub__(self, other):
        if __debug__: self.validate(other)
        if isinstance(other, EmptyFitness): return NotImplemented
        self.values = tuple((value1 - value2 for value1, value2 in izip(self.values, other.values)))
        return self
    
    def __mul__(self, other):
        if not isinstance(other, (int, float)): return NotImplemented
        result = (expected_type(value * other) for expected_type, value in izip(self.types, self.values))
        return type(self)(tuple(result), True)
    
    def __div__(self, other):
        if not isinstance(other, (int, float)): return NotImplemented
        result = (expected_type(value / other) for expected_type, value in izip(self.types, self.values))
        return type(self)(tuple(result), True)
    
    def __truediv__(self, other):
        if not isinstance(other, (int, float)): return NotImplemented
        result = (expected_type(value / other) for expected_type, value in izip(self.types, self.values))
        return type(self)(tuple(result), True)

#=======================================================================

class FitnessMaximise(Fitness):
    '''Represents a simple fitness value where higher values are
    considered to be more fit.
    '''
    pass

class FitnessMaximize(FitnessMaximise):
    '''Represents a simple fitness value where higher values are
    considered to be more fit.
    '''
    pass

#=======================================================================

class FitnessMinimise(Fitness):
    '''Represents a simple fitness value where lower values are
    considered to be more fit.
    '''
    def __gt__(self, other):
        '''Determines whether `self` is more fit than `other`.
        
        A `Fitness` instance is always more fit than ``None`` or any
        object which is not a `Fitness`.
        
        :Parameters:
          other : `Fitness`, ``None`` or another object
            The object to compare this `Fitness` instance to.
        
        :Returns:
            ``True`` if `self` is more fit than `other`; otherwise,
            ``False``.
        '''
        if not isinstance(other, Fitness): return True
        # By default, Python performs a lexicographical comparison on sequences.
        return self.values < other.values
    
    @property
    def simple(self):
        '''Returns the most significant part of the fitness value. This
        value is negated to ensure maximisation.
        '''
        return -self.values[0]
    

class FitnessMinimize(FitnessMinimise):
    '''Represents a simple fitness value where lower values are
    considered to be more fit.
    '''
    pass

#=======================================================================

class EmptyFitness(object):
    '''Represents an unspecified multi-stage fitness value.
    
    `EmptyFitness` is used in place of a default value for `Fitness`,
    since instances of classes derived from `Fitness` are only
    comparable if they are of the same derived type, and in place of
    ``None`` to avoid the need for specific tests.
    
    `EmptyFitness` always compares as less fit than a `Fitness` instance
    and equal to another `EmptyFitness`.
    
    Mathematical operations on `EmptyFitness` and `Fitness` instances
    create a default instance of the type of `Fitness` provided and use
    that in place of the `EmptyFitness`.
    '''
    
    #pylint: disable=R0201,W0613
    
    def __init__(self, other=None):
        pass
    
    def __str__(self):
        return ''
    
    @property
    def simple(self):
        '''Returns the most significant part of the fitness value.'''
        return 0
    
    @property
    def comma_separated(self):
        '''Returns the parts of the fitness value separated by commas.
        '''
        return '-'
    
    def __bool__(self):
        return False
    
    def __add__(self, other):
        if type(other) is EmptyFitness: return self
        else: return type(other)() + other
    
    def __sub__(self, other):
        if type(other) is EmptyFitness: return self
        else: return type(other)() - other
    
    def __radd__(self, other):
        if type(other) is EmptyFitness: return self
        else: return other + type(other)()
    
    def __rsub__(self, other):
        if type(other) is EmptyFitness: return self
        else: return other - type(other)()
    
    def __eq__(self, other): return isinstance(other, EmptyFitness)
    def __ne__(self, other): return not isinstance(other, EmptyFitness)
    def __ge__(self, other): return isinstance(other, EmptyFitness)
    def __gt__(self, other): return False
    def __le__(self, other): return True
    def __lt__(self, other): return True
    
    def __mul__(self, other): return self
    def __div__(self, other): return self
    def __truediv__(self, other): return self

#=======================================================================

_dominating_fitness_classes = { }

def _dominating_fitness_gt(self, other):
    '''Determines whether `self` dominates `other`. To dominate, every
    fitness value must be less (more negative) than or equal to the
    matching value in `other`.
    
    A `SimpleDominatingFitness` instance always dominates ``None`` or
    any object which is not a `SimpleDominatingFitness` with the same
    number of values.
    
    :Parameters:
      other : `SimpleDominatingFitness`, ``None`` or another object
        The object to compare this `SimpleDominatingFitness` instance
        to.
    
    :Returns:
        ``True`` if `self` dominates `other`; otherwise, ``False``.
    '''
    assert isinstance(self, Fitness), "_dominating_fitness_gt must be bound to a Fitness class."
    if isinstance(other, EmptyFitness): return True
    if not isinstance(other, type(self)): return False
    return all(i1 <= i2 for i1, i2 in izip(self.values, other.values))

def SimpleDominatingFitness(value_count=2):
    '''Returns a class suitable for a simple dominating fitness with the
    specified number of values. A fitness dominates another fitness if
    every value is less (more negative) than or equal to the other's.
    
    This function caches the classes returned, ensuring that, provided
    `value_count` is the same, the instances are comparable.
    
    Fitness values should be initialised as follows::
    
        fitness = SimpleDominatingFitness(2)([objective1, objective2])
    
    '''
    cls = _dominating_fitness_classes.get(value_count, None)
    if not cls:
        new_dict = dict(FitnessMinimise.__dict__)
        new_dict['types'] = [float] * value_count
        new_dict['defaults'] = [0.0] * value_count
        new_dict['__gt__'] = _dominating_fitness_gt
        cls = type('SimpleDominatingFitness%d' % value_count, (FitnessMinimise,), new_dict)
        _dominating_fitness_classes[value_count] = cls
    return cls

