# esec

An Evolutionary Computation (EC) framework for Python.

`esec` enables research of both simple and complex ecosystem models of evolutionary computation. It supports highly customisable evolutionary systems through the use of ESDL Evolutionary System Definition Language (ESDL).

A wide range of standard models and benchmark problems are included, such as real valued continuous optimisation, binary problem landscapes, tree-based genetic programming and Grammatical Evolution. *March 10: A new selection of Genetic Programming configurations have been added. These are (currently) only available in the repository.*

`esec` is written in the Python programming language and is compatible with CPython 2.6, [CPython 2.7](http://www.python.org/) (recommended), CPython 3.2 (after running [2to3.py](http://docs.python.org/library/2to3.html)), IronPython 2.6 and [IronPython 2.7](http://ironpython.net). The [Numpy](http://numpy.scipy.org/) and [Psyco](http://psyco.sourceforge.net/) packages may be used with CPython for extended functionality.

The `run.py` script provides an efficient command line interface to run single or multiple experiments using `esec`. All configuration information can be provided using command line arguments, however for research experiments the recommended method is to use a configuration or batch file.

Configuration files are based on Python dictionaries and contain all the settings necessary to conduct a single experiment. Batch files provide a sequence of configurations, allowing a multitude of experiments to be conducted automatically.

A graphical user interface for Windows is under development at [esecui](http://github.com/zooba/esecui), with preview executables now available (requires .NET Framework 4.0 or Mono 2.10).
