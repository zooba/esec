'''Provides a Python-based fluent interface for specifying algorithms.

To define a system, derive your class from `FluentSystem` and use its
instance functions to specify the code.

For example::

    class GAwithTournament(FluentSystem):
        def definitions(self):
            self.External("random_binary")
            self.External("default_evaluator")
            self.External("tournament")
            self.External("mutate_random")
            self.External("best")
        
            self.Group("population")
            self.Group("parents")
            self.Group("offspring")

            self.Variable("size")

            self.Block('generation')
    
        def block_init(self):
            self.Assign("size", 100.0)

            self.From(self.Generator("random_binary", length=10.0)) \
                .Select(self.Group("population", "size"))

            self.Eval("population", "default_evaluator")
            self.Yield("population")

        def block_generation(self):
            self.From("population") \
                .Select(self.Group("parents", limit="size")) \
                .Using(self.Function("tournament", k=2.0))
            self.From("parents") \
                .Select("offspring") \
                .Using(self.Function("mutate_random", per_gene_rate=0.1))

            self.From("population", "offspring") \
                .Select(self.Group("population", limit="size")) \
                .Using("best")

            self.Yield("population")

'''
# Disable warnings about invalid names.
#pylint: disable=C0103

from esdlc.model import System
from esdlc.model.components import *    #pylint: disable=W0401,W0614

__all__ = ['FluentSystem']

class PartialUsingStmt(object):
    '''Returned by `PartialFromStmt` and `PartialJoinStmt` to provide
    the `Using` term in those statements.
    '''
    def __init__(self, owner):
        self.owner = owner

    def Using(self, *operators):
        '''Specify the operators for the current ``FROM`` or ``JOIN``
        statment.
        '''
        self.owner.operators.extend(operators)

class PartialFromStmt(object):
    '''Returned by `FluentSystem.From` to represent a partially
    constructed ``FROM-SELECT`` statement.
    '''
    def __init__(self, system, sources):
        self.system = system
        self.sources = list(sources)
        self.destinations = []
        self.operators = []

    def Select(self, *destinations):
        '''Specify the destination groups, either as strings or through
        `FluentSystem.Group`.
        '''
        self.destinations.extend(destinations)
        return PartialUsingStmt(self)
    
    def complete(self):
        '''Completes the statement. This is for internal use only.
        '''
        srcs = [self.system.Group(i) if isinstance(i, str) else i for i in self.sources]
        src = Merge(srcs)

        for op in self.operators:
            if isinstance(op, str): op = self.system.Function(op)
            src = Operator(src, op)

        dests = [self.system.Group(i) if isinstance(i, str) else i for i in self.destinations]
        return Store(src, dests)

class PartialJoinStmt(object):
    '''Returned by `FluentSystem.Join` to represent a partially
    constructed ``JOIN-INTO`` statement.
    '''
    def __init__(self, system, sources):
        self.system = system
        self.sources = list(sources)
        self.destinations = []
        self.operators = []

    def Into(self, *destinations):
        '''Specify the destination groups, either as strings or through
        `FluentSystem.Group`.
        '''
        self.destinations.extend(destinations)
        return PartialUsingStmt(self)
    
    def complete(self):
        '''Completes the statement. This is for internal use only.
        '''
        srcs = [self.system.Group(i) if isinstance(i, str) else i for i in self.sources]
        src = Join(srcs)

        for op in self.operators:
            if isinstance(op, str): op = self.system.Function(op)
            src = Operator(src, op)

        dests = [self.system.Group(i) if isinstance(i, str) else i for i in self.destinations]
        return Store(src, dests)

class FluentSystem(System):
    '''Represents a system specified using a fluent interface. The
    instance methods may be used to specify statements.
    '''
    def __init__(self):
        super(FluentSystem, self).__init__()
        self.__stmt = None
        self.__isdef = True
        self._statements = []
        self.definitions()
        self.__isdef = False
        self.blocks[self.INIT_BLOCK_NAME] = self._statements = []
        self.block_init()
        if self.__stmt:
            self._statements.append(self.__stmt)
            self.__stmt = None
        self._statements = None

        for key, value in self.blocks.iteritems():
            if key != '_init':
                self._statements = value
                getattr(self, 'block_' + key)()
                if self.__stmt:
                    self._statements.append(self.__stmt)
                    self.__stmt = None
                self._statements = None

    def definitions(self):
        '''Override this method to specify definitions.

        All blocks apart from `block_init` must be specified in this
        function, for example::

            def definitions(self):
                self.Block("Generation")

            def block_generation(self):
                ...
        '''
        raise NotImplementedError()

    def block_init(self):
        '''Override this method to specify the initialisation block.
        '''
        raise NotImplementedError()

    def _complete_stmt(self):
        '''Completes the current statement, if any.'''
        if self.__stmt:
            try:
                self._statements.append(self.__stmt.complete())
            except AttributeError:
                self._statements.append(self.__stmt)
        self.__stmt = None

    def Block(self, name):
        '''Specify a named block. The name is required and is
        case-insensitive. Each block defined with this requires a
        member function with the name ``block_<name>``.
        
        An error occurs if this is called outside of `definitions`.
        '''
        assert self.__isdef, "Cannot specify blocks outside of definitions()"
        name = name.lower()
        self.blocks[name] = []
        self.block_names.append(name)

    def Repeat(self, func, count):
        '''Specify a repeat block. The `func` is a reference to a
        method bound to this system containing statements. The `count`
        is a variable name, a number or the result of calling one of
        `Variable`, `External`, `Constant`, `Function` or
        `RPNExpression`.

        An error occurs if this is called within `definitions`.

        For example::

            def block_generation(self):
                ...
                self.Repeat(self.repeat_block, 100)
                ...
        
            def repeat_block(self):
                ...
        '''
        assert not self.__isdef, "Cannot specify repeat blocks within definitions()"
        self._complete_stmt()
        block_statements = self._statements
        
        self._statements = []
        self.__stmt = None
        func()
        self._complete_stmt()

        if isinstance(count, str): count = self.Variable(count)
        elif isinstance(count, (int, float)): count = self.Constant(count)

        block_statements.append(RepeatBlock(self._statements, count))
        self._statements = block_statements

    def Group(self, name, limit=None, span=None):
        '''Specify a named group. The `name` is case-insensitive. All
        groups must be specified initially within `definitions` before
        they may be referenced elsewhere.

        If called within `definitions`, `limit` must be ``None``.
        
        If called outside `definitions`, `limit` may be the name of a
        variable, a number or the result of calling one of `Variable`,
        `External`, `Constant`, `Function` or `RPNExpression`. The
        returned value is a group reference.
        '''
        name = name.lower()
        if self.__isdef:
            assert limit is None
            self.variables[name] = Variable(name, span=span)
        else:
            if isinstance(limit, str):
                limit = self.Variable(limit)
            elif isinstance(limit, (int, float)):
                limit = self.Constant(limit)

            return GroupRef(self.variables[name], limit=limit, span=span)

    def Generator(self, name, span=None, **parameters):
        '''Specify a generator. Generators do not need to be specified
        in `definitions`. The values in `parameters` may be variable
        names, numbers, the result of calling one of `Variable`,
        `External`, `Constant`, `Function` or `RPNExpression`, or
        ``None`` to specify an implicit parameter.
        '''
        return self.Function(name, span, **parameters)
    
    def Variable(self, name, value=None, span=None):
        '''Specify a variable. Variables must be specified in
        `definitions` before they may be accessed elsewhere. `value`
        is ignored outside of `definitions`.

        If no variable with a matching name exists, an external with a
        matching name will be returned, if any.
        '''
        name = name.lower()
        if self.__isdef:
            var = Variable(name=name, value=value)
            self.variables[name] = var
        else:
            var = self.variables.get(name) or self.externals.get(name)
            assert var, "Variable `%s` is not defined" % name
            return VariableRef(var, span=span)
    
    def Constant(self, value, span=None):
        '''Specify a constant. Constants do not need to be specified in
        `definitions`.
        '''
        var = Variable(value=value, constant=True)
        self.constants.append(var)
        return VariableRef(var, span=span)
    
    def External(self, name, value=None, span=None):
        '''Specify an external. Externals do not need to be specified
        in `definitions`.
        '''
        name = name.lower()
        var = self.externals.get(name)
        if not var or self.__isdef:
            var = Variable(name=name, value=value, external=True)
            self.externals[name] = var
        return None if self.__isdef else VariableRef(var, span=span)

    def RPNExpression(self, expr, span=None):
        '''Constructs an arithmetic expression from reverse-Polish
        notation.
    
        Supported operators are ``+-*/^%~``, where ``~`` is the unary
        ``-`` operator.

        For example::

            self.Assign("x", self.RPNExpression("m x * c +"))

        is equivalent to::

            x = m * x + c

        '''
        assert not self.__isdef, "Cannot specify expressions within definitions()."
        
        stack = []
        for token in expr.split(' '):
            if not token:
                continue
            elif len(token) == 1 and token in '+-*/^%':
                right = stack.pop()
                if type(right) is float: right = self.Constant(right, span=span)
                elif type(right) is str: right = self.Variable(right, span=span)
                if stack:
                    left = stack.pop()
                    if type(left) is float: left = self.Constant(left, span=span)
                    elif type(left) is str: left = self.Variable(left, span=span)
                    stack.append(BinaryOp(left, token, right, span=span))
                else:
                    stack.append(UnaryOp(token, right, span=span))
            elif token == '.':
                attrib = stack.pop()
                source = stack.pop()
                if type(source) is float: source = self.Constant(source, span=span)
                elif type(source) is str: source = self.Variable(source, span=span)
                stack.append(VariableRef(Function.getattrib(source, attrib, span=span), span=span))
            elif token == '~':
                right = stack.pop()
                if type(right) is float: right = self.Constant(right, span=span)
                elif type(right) is str: right = self.Variable(right, span=span)
                stack.append(UnaryOp('-', right, span=span))
            else:
                try:
                    value = float(token)
                    stack.append(value)
                except ValueError:
                    stack.append(token)
        return stack.pop()

    def Pragma(self, text, span=None):
        '''Specifies a pragma.
        
        An error occurs if this is called within `definitions`.
        '''
        assert not self.__isdef, "Cannot specify pragmas within definitions()."
        self._complete_stmt()
        self._statements.append(Pragma(text, span=span))

    def Assign(self, dest, source, span=None):
        '''Specifies an assignment of `source` to `dest`. Both `source`
        and `dest` may be variable names or the returned value of
        `Variable`, and `dest` may also be a number of the returned
        value of `Constant`, `External`, `Function` or `RPNExpression`.

        Constants, externals and expressions cannot be assigned to.

        An error occurs if this is called within `definitions`.
        '''
        assert not self.__isdef, "Cannot specify assignments within definitions()."

        self._complete_stmt()
        if isinstance(dest, str): dest = self.Variable(dest)
        if isinstance(source, str): source = self.Variable(source)
        elif isinstance(source, (int, float)): source = self.Constant(source)

        self.__stmt = Function.assign(dest, source, span)

    def Function(self, name, span=None, **parameters):
        '''Specifies a function call. The `name` must be a string or
        the value returned by `External`; calling `Function` within
        `definitions` behaves identically to calling `External` with
        the same `name`.

        The values in `parameters` may be variable names, numbers, the
        result of calling one of `Variable`, `External`, `Constant`,
        `Function` or `RPNExpression`, or ``None`` to specify an
        implicit parameter.
        '''
        if self.__isdef:
            self.External(name)
        else:
            if isinstance(name, str):
                name = self.External(name, span=span)
            params = { }
            for key, value in parameters.iteritems():
                if value is None:
                    params[key] = None
                elif isinstance(value, VariableRef):
                    params[key] = value
                elif isinstance(value, (Function, Variable)):
                    params[key] = VariableRef(value, span=span)
                else:
                    params[key] = self.Constant(value, span=span)
            
            return Function.call(source=name, parameter_dict=params, span=span)

    def From(self, *sources):
        '''Begins a ``FROM-SELECT`` statement. Each group and operator
        name may be specified as a string or the value returned by
        `Group` or `Generator`.

        The ``Select`` function on the returned object should be called
        to complete the statement. The ``Using`` function on that
        returned object may optionally be called to specifiy operators.

        For example::

            self.From("source").Select(self.Group("destination", limit=100))
        '''
        self._complete_stmt()
        self.__stmt = PartialFromStmt(self, sources)
        return self.__stmt

    def Join(self, *sources):
        '''Begins a ``JOIN-INTO`` statement. Each group and operator
        name may be specified as a string or the value returned by
        `Group` or `Generator`.

        The ``Into`` function on the returned object should be called
        to complete the statement. The ``Using`` function on that
        returned object may optionally be called to specifiy operators.

        For example::

            self.Join("A", "B").Into("merged").Using("tuples")
        '''
        self._complete_stmt()
        self.__stmt = PartialJoinStmt(self, sources)
        return self.__stmt

    def Eval(self, *sources):
        '''Specifies an ``EVAL`` statement. Each group name may be
        specified as a string or the value returned by `Group`.

        If the last item is a string that is not a known group or was
        returned by `Function`, it is assumed to be the evaluator.
        '''
        self._complete_stmt()
        
        srcs = list(sources)
        evaluator = srcs.pop()
        if isinstance(evaluator, GroupRef):
            srcs.append(evaluator)
            evaluator = None
        elif isinstance(evaluator, str):
            if evaluator in self.variables:
                srcs.append(evaluator)
                evaluator = None
            else:
                evaluator = self.Function(evaluator)

        srcs = [self.Group(i) if isinstance(i, str) else i for i in srcs]
        self.__stmt = EvalStmt(srcs, [evaluator])

    def Yield(self, *sources):
        '''Specifies a ``YIELD`` statement. Each group name may be
        specified as s tring or the value returned by `Group`.
        '''
        self._complete_stmt()

        srcs = []
        for i in sources:
            if isinstance(i, str):
                srcs.append(self.Group(i))
            else:
                srcs.append(i)

        self.__stmt = YieldStmt(srcs)
        return None