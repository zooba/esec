'''Performs validation of semantic model instances.
'''

import re
import warnings
from esdlc.model.components import *        #pylint: disable=W0401,W0614
from esdlc.model.components.lists import *  #pylint: disable=W0401,W0614
import esdlc.errors as error

class Validator(object):
    '''Validates a semantic model instance and generates relevant
    error messages.
    '''
    def __init__(self, system=None):
        self.system = system
        self._errors = []
        self._known_names = { }

        if system is not None:
            for stmts in self.system.blocks.itervalues():
                self._verify_stmts(stmts)

            self._errors = list(sorted(set(self._errors)))

    @property
    def all(self):
        '''Returns a list of errors and warnings in the provided model.
        '''
        return list(self._errors)
    
    @property
    def errors(self):
        '''Returns a list of errors in the provided model.'''
        return [i for i in self._errors if not i.iswarning]

    @property
    def warnings(self):
        '''Returns a list of warnings for the provided model.'''
        return [i for i in self._errors if i.iswarning]

    def __nonzero__(self):
        return not any(not i.iswarning for i in self._errors)

    def _verify_stmts(self, stmts):
        '''Verifies all the statements in `stmts`.'''
        for stmt in stmts:
            tag = type(stmt).__name__.lower()
            if tag == 'repeatblock':
                self._verify_stmts(stmt.statements)
            elif tag == 'function':
                self._verify_function(stmt)
            elif tag == 'store':
                self._verify_store(stmt)
            elif tag == 'yieldstmt':
                self._verify_yield(stmt)
            elif tag == 'evalstmt':
                self._verify_eval(stmt)
            elif tag == 'pragma':
                self._verify_pragma(stmt)
            else:
                assert False, "Invalid statement: %s" % stmt
                self._errors.append(error.InvalidSyntaxError(stmt.span))
    
    def _verify_functionlist(self, functions):
        '''Verifies the functions in a function list.'''
        assert isinstance(functions, FunctionList)
        for func in functions:
            self._verify_function(func)

    def _verify_expression(self, expr):
        '''Verifies an arithmetic expression tree.'''
        tag = type(expr).__name__.lower()
        
        if tag == 'variableref':
            self._verify_variable(expr.id, expr.span)
        elif tag == 'function':
            self._verify_function(expr)
        elif tag == 'binaryop':
            self._verify_expression(expr.left)
            self._verify_expression(expr.right)
        elif tag == 'unaryop':
            self._verify_expression(expr.right)
        elif tag in set(('groupref', 'variable')):
            raise error.InvalidSyntaxError(expr.span)
        else:
            warnings.warn("Unhandled expression node %s (%r)" % (expr, expr))
            raise error.InvalidSyntaxError(expr.span)

    def _verify_parameterlist(self, parameters, valid_parameters=None):
        '''Verifies the parameters in a parameter list.'''
        assert isinstance(parameters, ParameterList)
        valid_parameters = valid_parameters or []
        seen = set()
        for param in parameters:
            if param.name in seen:
                self._errors.append(error.RepeatedParameterNameError(param.span, param.name))
            seen.add(param.name)
            
            if param.name.startswith('_') and param.name not in valid_parameters:
                self._errors.append(error.InternalParameterNameError(param.span, param.name))
            
            if param.value is not None:
                try:
                    self._verify_expression(param.value)
                except error.InvalidSyntaxError:
                    self._errors.append(error.InvalidFunctionCallError(param.span))

    def _verify_variable(self, var, span=None):
        '''Verifies a variable.'''
        if isinstance(var, Function):
            return self._verify_function(var)

        assert isinstance(var, Variable), repr(var)
        
        if var.external:
            if var.name not in self.system.externals:
                self._errors.append(error.UninitialisedGlobalError(span or var.span, var.name))
        elif var.constant:
            pass
        else:
            if var.name not in self.system.variables:
                self._errors.append(error.UninitialisedVariableError(span or var.span, var.name))
            if var.name in self.system.blocks:
                self._errors.append(error.AmbiguousVariableBlockNameError(span or var.span, var.name))

        if var.name and var.name.startswith('_'):
            self._errors.append(error.InternalVariableNameError(span or var.span, var.name))
        elif var.name and not var.constant and not re.match('^(?!\d)\w+$', var.name, re.IGNORECASE):
            self._errors.append(error.InvalidVariableError(span or var.span, var.name))

    def _verify_function(self, stmt):
        '''Verifies a function call.'''
        src = None    
        if stmt.name == '_call':
            self._verify_parameterlist(stmt.parameters, valid_parameters=set(('_function',)))
            src = stmt.parameter_dict['_function']
            # src is validated below
        elif stmt.name == '_getattrib':
            params = stmt.parameter_dict
            src, attrib = params['_source'], params['_attrib']
            assert isinstance(attrib, str), repr(stmt)
            # src is validated below
        elif stmt.name == '_getindex':
            params = stmt.parameter_dict
            src, index = params['_source'], params['_index']
            try:
                self._verify_expression(index)
            except error.InvalidSyntaxError:
                self._errors.append(error.ExpectedIndexError(index.span))
            # src is validated below
        elif stmt.name == '_assign':
            params = stmt.parameter_dict
            src, dest = params['_source'], params['_destination']
            try:
                self._verify_expression(src)
            except error.InvalidSyntaxError:
                self._errors.append(error.InvalidAssignmentError(src.span))
            if (isinstance(dest, VariableRef) and isinstance(dest.id, Variable)
                and not dest.id.external and not dest.id.constant):
                self._verify_variable(dest.id, dest.span)
            else:
                self._errors.append(error.InvalidAssignmentError(stmt.span))
            src = None
        else:
            self._errors.append(error.InvalidFunctionCallError(stmt.span))
        
        if src is not None:    
            assert isinstance(src, VariableRef), repr(src)
            self._verify_variable(src.id, src.span)

    def _verify_grouplist(self, groups):
        '''Verifies a group list and the groups within it.'''
        assert isinstance(groups, GroupList), repr(groups)

        seen_unlimited = False
        seen = set()
        for i in groups:
            try: limit = i.limit
            except AttributeError: limit = None
            if groups.allow_sizes:
                if seen_unlimited:
                    self._errors.append(error.InaccessibleGroupError(i.span, str(i)))
                seen_unlimited = seen_unlimited or (limit is None)
                if limit is not None:
                    try:
                        self._verify_expression(limit)
                    except error.InvalidSyntaxError:
                        self._errors.append(error.InvalidGroupSizeError(limit.span))
            elif limit is not None:
                self._errors.append(error.UnexpectedGroupSizeError(i.span, i.id.name))
            
            if isinstance(i, GroupRef):
                self._verify_group(i.id, i.span)
                if groups.repeats_error and i.id.name in seen:
                    self._errors.append(groups.repeats_error(i.span, i.id.name))
                seen.add(i.id.name)
            elif isinstance(i, Function):
                if groups.allow_generators: self._verify_function(i)
                else: self._errors.append(error.GeneratorAsDestinationError(i.span))
            elif isinstance(i, Stream):
                if groups.allow_streams: self._verify_stream(i)
                else: self._errors.append(error.InvalidGroupError(i.span))
            else:
                self._errors.append(error.ExpectedGroupError(i.span))

    def _verify_operator(self, stmt):
        '''Verifies an operator instance and its internal function
        call.
        '''
        assert isinstance(stmt, Operator), repr(stmt)
        if stmt.func.name != '_call':
            self._errors.append(error.InvalidFunctionCallError(stmt.func.span))
        else:
            self._verify_parameterlist(stmt.func.parameters, valid_parameters=set(('_function', '_source')))
            func = stmt.func.parameter_dict['_function']
            assert isinstance(func, VariableRef), repr(func)
            self._verify_variable(func.id, func.span)
        self._verify_stream(stmt.source)

    def _verify_group(self, group, span=None):
        '''Verifies a group.'''
        assert isinstance(group, Variable), repr(group)
        if group.name in self.system.externals:
            self._errors.append(error.AmbiguousGroupGeneratorNameError(span or group.span, group.name))
        elif group.name not in self.system.variables:
            self._errors.append(error.InvalidGroupError(span or group.span, group.name))
        if group.name in self.system.blocks:
            self._errors.append(error.AmbiguousVariableBlockNameError(span or group.span, group.name))

    def _verify_stream(self, stmt):
        '''Verifies a stream.'''
        if isinstance(stmt, Stream):
            self._verify_stream(stmt.source)
        elif isinstance(stmt, Operator):
            self._verify_operator(stmt)
        elif isinstance(stmt, (Merge, Join)):
            self._verify_grouplist(stmt.sources)
        elif isinstance(stmt, GroupRef):
            self._verify_group(stmt.id)
        else:
            assert False, repr(stmt)

    def _verify_store(self, stmt):
        '''Verifies a store operation.'''
        assert isinstance(stmt, Store), repr(stmt)
        self._verify_grouplist(stmt.destinations)
        self._verify_stream(stmt.source)
    
    def _verify_yield(self, stmt):
        '''Verifies a yield operation.'''
        assert isinstance(stmt, YieldStmt), repr(stmt)
        self._verify_grouplist(stmt.sources)

    def _verify_eval(self, stmt):
        '''Verifies an evaluation operation.'''
        assert isinstance(stmt, EvalStmt), repr(stmt)
        self._verify_grouplist(stmt.sources)

    def _verify_pragma(self, stmt):
        '''Verifies a pragma.'''
        pass
