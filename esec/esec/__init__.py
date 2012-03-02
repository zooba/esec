'''.. title:: esec - An EcoSystem Evolutionary Computation Framework

.. include:: epydoc_include.txt

========
Overview
========

The |esec| Python package was created to enable research of ecosystem
models of evolutionary computation. It includes support for classic
models such as Genetic Algorithms and Evolutionary Strategies as well as
the use of complex topographical structures. A wide range of standard
models and benchmark problems are included, such as real valued
continuous optimisation and binary problem landscapes.

|esec| is written in the Python programming language and is compatible
with CPython 2.6, `CPython 2.7`_, `IronPython 2.6.1`_ and
IronPython 2.7.

.. _`CPython 2.7`: http://www.python.org/
.. _`IronPython 2.6.1`: http://ironpython.codeplex.com/

|esec|'s model of evolutionary computation is primarily based on species
(see `esec.species`), landscapes (see `esec.landscape`) and systems_.

Species
-------
A species defines the representation and breeding operations of a
population. Genotype-phenotype mapping is also implemented, where
possible, as a property of a species.

Implementing a new representation always requires the creation of a new
species, potentially using an existing species as the underlying
representation.

Landscapes
----------
A landscape provides the specific parameters of the search domain
without necessarily being strictly coupled to a particular species.
The phenotype of an individual, as provided by the species definition,
is passed to an evaluation function that determines the fitness of the
individual. Each new problem requires that a new landscape is created.

Systems
-------
Systems describe the breeding process using Evolutionary System
Definition Language (ESDL). ESDL allows complex combinations of
selection, breeding and evaluation to be expressed in a clear, efficient
manner that is not tied to any particular implementation.
A detailed explanation of the syntax and use of ESDL is available at
|esdl_url|.

The following example illustrates using ESDL to initialise and breed a
population using a simple generational model::
  
  FROM random_int SELECT 100 population
  YIELD population
  
  BEGIN generation
    FROM population SELECT 100 parents USING binary_tournament
    FROM parents    SELECT recombined  USING crossover_one
    FROM recombined SELECT population  USING mutate_random(per_gene_prob=0.05)
    YIELD population
  END generation

The `Experiment` class is used to run single experiments in |esec|.
Multiple experiments are conducted by instantiating and executing
multiple `Experiment` instances. (Multiple experiments may only be run
simultaneously if they are on separate threads; thread-local storage is
used for storing some global objects.)

.. packagetree:: esec
   :style: UML

'''
__docformat__ = 'restructuredtext'

from esec.individual import OnIndividual

GLOBAL_ESDL_FUNCTIONS = { }

class _esdl_func(object):       #pylint: disable=R0903
    '''Delayed handling for named or parameterised instances of the
    `esdl_func` decorator.
    '''
    def __init__(self, *names, **kwargs):
        self.names = names
        self.on_individual = kwargs.get('on_individual', False)
    
    def __call__(self, func):
        if self.on_individual:
            if self.names:
                for name in self.names:
                    GLOBAL_ESDL_FUNCTIONS[name] = OnIndividual(name, func)
            else:
                GLOBAL_ESDL_FUNCTIONS[func.__name__] = OnIndividual(func.__name__, func)
        else:
            if self.names:
                for name in self.names:
                    GLOBAL_ESDL_FUNCTIONS[name] = func
            else:
                GLOBAL_ESDL_FUNCTIONS[func.__name__] = func
        return func

def esdl_func(*names, **kwargs):
    '''A function decorator that exposes an unbound function within an
    ESDL system.
    
    If specified, `names` is a tuple of strings specifying the aliases
    by which the function may be accessed. If unspecified, the
    ``__name__`` member of the function object is used instead.
    
    The named parameter ``on_individual``, if ``True``, produces an
    `OnIndividual` object for each alias with the wrapped function as 
    the default. If unspecified, this is assumed to be ``False``.
    '''
    if len(names) == 1 and hasattr(names[0], '__call__'):
        return _esdl_func(**kwargs)(names[0])
    else:
        return _esdl_func(*names, **kwargs)

class esdl_eval(object):
    '''A function decorator that produces an evaluator object.
    
    For example, specifying::
    
        @esdl_eval
        def onemax(indiv):
            return sum(indiv)
    
    is equivalent to::
    
        class onemax_class(object):
            def eval(self, indiv):
                return sum(indiv)
        
        onemax = onemax_class()
    
    A ``prepare`` method may be subsequently specified by using the
    `pre` member of the evaluator object to decorate the function.
    
    For example, given the previous example, specifying::
    
        @onemax.pre
        def onemax(indiv):
            # start calculation
    
    is equivalent to::
    
        class onemax_class(object):
            # eval as above
            
            def prepare(self, indiv):
                # start calculation
    
    An evaluator specified with this is automatically included in the
    ESDL system. Note that, unlike `esdl_func`, an alternative name can
    not be specified.
    '''
    def __init__(self, func):
        '''Initialises the ``eval`` member of the evaluator with the
        provided function.
        '''
        self._eval = func
        self._prepare = None
        self._legal = None
        GLOBAL_ESDL_FUNCTIONS[func.__name__] = self
    
    def __repr__(self):
        '''Displays the evaluator using the repr of the underlying
        function.
        '''
        return "<%s evaluator at 0x%08x>" % (self._eval.__name__, id(self))

    def __call__(self):
        '''Returns ourself, in case someone tries to reinstantiate us.'''
        return self

    def __str__(self):
        '''Displays the evaluator using the str of the underlying
        function.
        '''
        return repr(self)
    
    def eval(self, indiv):
        '''Evaluates the provided `indiv`.'''
        return self._eval(indiv)

    def prepare(self, indiv):
        '''Prepares the evaluator to potentially evaluate `indiv`.'''
        if self._prepare: self._prepare(indiv)
    
    def legal(self, indiv):
        '''Determines whether `indiv` is legal for this evaluator.
        
        If `indiv` is callable, this is assumed to be being used as a
        decorator.
        '''
        if hasattr(indiv, '__call__'):
            self._legal = indiv
            return self
        elif self._legal:
            return self._legal(indiv)
        else:
            return True
    
    def pre(self, func):
        '''Initialises the ``prepare`` member of the evaluator with the
        provided function.
        '''
        self._prepare = func
        return self

from esec.experiment import Experiment
import esec.landscape

