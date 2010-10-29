'''.. title:: esec - An EcoSystem Evolutionary Computation Framework

.. include:: epydoc_include.txt

========
Overview
========

The |esec| Python package was created to enable research of ecosystem models of
evolutionary computation.
It includes support for classic models such as Genetic Algorithms and
Evolutionary Strategies as well as the use of complex topographical structures.
A wide range of standard models and benchmark problems are included, such as
real valued continuous optimisation and binary problem landscapes.

|esec| is written in the Python programming language and is compatible with
CPython 2.6, `CPython 2.7`_, `IronPython 2.6.1`_ and `IronPython 2.7`_.

.. _`CPython 2.7`: http://www.python.org/
.. _`IronPython 2.6.1`: http://ironpython.codeplex.com/
.. _`IronPython 2.7`: http://ironpython.net/

|esec|'s model of evolutionary computation is primarily based on species (see
`esec.species`), landscapes (see `esec.landscape`) and systems_.

Species
-------
A species defines the representation and breeding operations of a population.
Genotype-phenotype mapping is also implemented, where possible, as a property
of a species.

Implementing a new representation always requires the creation of a new species,
potentially using an existing species as the underlying representation.

Landscapes
----------
A landscape provides the specific parameters of the search domain without
necessarily being strictly coupled to a particular species.
The phenotype of an individual, as provided by the species definition, is
passed to an evaluation function that determines the fitness of the individual.
Each new problem requires that a new landscape is created.

Systems
-------
Systems describe the breeding process using Evolutionary System Definition
Language (ESDL).
ESDL allows complex combinations of selection, breeding and evaluation to be
expressed in a clear, efficient manner that is not tied to any particular
implementation.
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

The `Experiment` class is used to run single experiments in |esec|. Multiple
experiments are conducted by instantiating and executing multiple `Experiment`
instances. (Multiple experiments may only be run simultaneously if they are on
separate threads; thread-local storage is used for storing some global objects.)

.. packagetree:: esec
   :style: UML

'''
__docformat__ = 'restructuredtext'

from esec.experiment import Experiment
import esec.landscape
