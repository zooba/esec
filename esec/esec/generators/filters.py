'''A set of filter generators that return some or all of a group of
individuals without modification.

These are distinct from `esec.generators.selectors` because they do not
compare individuals against each other (as in ``Best`` or ``Yougest``
selectors). Filters should always operate on unbounded groups.
'''

from esec import esdl_func

class NoReplacementFilter(object):
    '''An internal iterator class that supports filtering of the 'rest'
    of the population.
    
    It is used to optimise population partitioning by allowing, for
    example, five individuals to be selected at random and the remainder
    to be kept in a separate group.
    '''
    def __init__(self, _source, func):
        '''Initialises the iterator.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`Individual`)
            A sequence of individuals. This sequence is never cached or
            accessed by index.
          
          func : function(self, _source) |rArr| index
            A function that takes a list of individuals and returns the
            index of the next one selected.
        '''
        self._source = _source
        self.func = func
    
    def __iter__(self): return self
    
    def __getattribute__(self, name):
        if name.startswith('__'):
            pass
        elif name == 'rest' and hasattr(self._source, 'rest'):
            return self.__dict__['rest']
        
        return object.__getattribute__(self, name)
    
    def rest(self):
        '''Returns all remaining individuals in the group.'''
        if hasattr(self._source, 'rest'):
            return [indiv for indiv in self._source.rest() if self.func(indiv)]
        else:
            return (indiv for indiv in self._source if self.func(indiv))
    
    def next(self):
        '''Returns the next acceptable individual in the group.'''
        if not self._source: raise StopIteration
        
        while True:
            indiv = next(self._source)
            if self.func(indiv):
                return indiv


@esdl_func('unique')
def Unique(_source):
    '''Returns a sequence of the unique individuals based on phenomes.
    
    Individuals are compared using their ``phenome_string`` property.
    
    :Parameters:
      _source : iterable(`Individual`)
        A sequence of individuals. Some or all individuals are returned
        from this sequence, depending on the selection criteria.
    '''
    known = set()
    
    for indiv in _source:
        phenome = indiv.phenome_string
        if phenome not in known:
            known.add(phenome)
            yield indiv

@esdl_func('legal')
def Legal(_source):
    '''Returns all legal individuals. Legality is tested using the
    species' and the evaluator's ``legal(indiv)`` method. If either
    method does not exist, its result is assumed to be ``True``.
    '''
    
    return NoReplacementFilter(_source, lambda indiv: indiv.legal())

@esdl_func('illegal')
def Illegal(_source):
    '''Returns all illegal individuals. Legality is tested using the
    species' and the evaluator's ``legal(indiv)`` method. If either
    method does not exist, its result is assumed to be ``True``.
    '''
    
    return NoReplacementFilter(_source, lambda indiv: not indiv.legal())
