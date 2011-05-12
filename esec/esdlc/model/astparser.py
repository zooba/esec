'''Provides a conversion from an abstract syntax tree into a fully
instantiated semantic model.

This class is primarily used internally via the `esdlc.compileESDL`
function.
'''
from warnings import warn
from esdlc.model import System
from esdlc.model.components import *    #pylint: disable=W0401,W0614

class AstSystem(System):
    '''Represents a system implemented based on an abstract syntax
    tree.
    
    :Parameters:
      ast : esdlc.ast.AST instance
        The abstract syntax tree to generate the semantic model from.

      externals : dictionary of string-value pairs
        Variables which are defined externally. Values may be ``None``
        if they will be specified later (before execution).
    '''
    def __init__(self, ast=None, externals=None):
        super(AstSystem, self).__init__()
        self.ast = None    
        self._active = None
        
        if externals is not None:
            self.externals.update((name, Variable(name=name, value=value, external=True))
                                  for name, value in externals.iteritems())
        if ast is not None:
            self.read(ast)
        
    def read(self, ast):
        '''Reads an abstract syntax tree into the model.

        This function may be called once only for each instance of
        `AstSystem`; otherwise a ``RuntimeError`` is raised.
        '''
        if self.ast is not None:
            raise RuntimeError("Cannot call AstSystem.read() multiple times.")
        if ast.errors:
            raise ValueError("AST contains errors.")
        self.ast = ast

        blocks = []
        init_block = []
        blocks.append((self.INIT_BLOCK_NAME, init_block))
        
        for stmt in ast.expr:
            if stmt is None:
                pass
            elif stmt.category != 'block':
                if init_block is not None:
                    init_block.append(stmt)
                else:
                    pass
            else:
                init_block = None
                blocks.append((stmt.data, stmt.expr))
        
        for block_name, statements in blocks:
            self.block_names.append(block_name)
            self._active = self.blocks[block_name] = []
            self._visit_block(statements)

    def _add(self, item):
        '''Adds `item` to the active block.'''
        assert self._active is not None, "Invalid state for `_add()`"
        self._active.append(item)

    def _visit_block(self, statements):
        '''Visits each of `statements`.'''
        for stmt in statements:
            self._visit_stmt(stmt)

    def _repeatblock(self, block):
        '''Handles REPEAT blocks.'''
        count_expr = self._expression(block.data)
        previous = self._active
        self._active = stmts = []
        self._visit_block(block.expr)
        self._active = previous
        return RepeatBlock(stmts, count_expr)

    def _visit_stmt(self, stmt):
        '''Dispatches control to the appropriate handler for `stmt`.'''
        if stmt.category == 'op':
            self._add(self._expression(stmt))
        elif stmt.category == 'assign':
            self._add(self._assignment(stmt))
        elif stmt.category == 'UsingStmt':
            assert stmt.left is not None, repr(stmt)
            assert stmt.left.category in set(('SelectStmt', 'IntoStmt', 'EvalStmt')), repr(stmt.left)
            if stmt.left.category == 'SelectStmt':
                self._add(self._fromstmt(stmt))
            elif stmt.left.category == 'IntoStmt':
                self._add(self._joinstmt(stmt))
            else:
                self._add(self._evalstmt(stmt))
        elif stmt.category == 'SelectStmt':
            self._add(self._fromstmt(stmt))
        elif stmt.category == 'IntoStmt':
            self._add(self._joinstmt(stmt))
        elif stmt.category == 'EvalStmt':
            self._add(self._evalstmt(stmt))
        elif stmt.category == 'YieldStmt':
            self._add(self._yieldstmt(stmt))
        elif stmt.tag == 'REPEAT':
            self._add(self._repeatblock(stmt))
        elif stmt.category == 'pragma':
            self._add(Pragma(stmt.tag[1:], stmt.tokens))
        else:
            warn('Unhandled statement type: %r' % stmt)

    def _assignment(self, node):
        '''Handles assignment nodes.'''
        assert node.category == 'assign', repr(node)
        return Function.assign(self._expression(node.left), self._expression(node.right), node.fulltokens)

    def _expression(self, node):
        '''Handles expression nodes.'''
        expr = None
        if node.category == 'expr':
            assert len(node.expr) == 1, repr(node.expr)
            expr = self._expression(node.expr[0])
        elif node.category == 'op':
            if node.left is None:
                expr = UnaryOp(node.tag, self._expression(node.right), span=node.fulltokens)
            else:
                expr = BinaryOp(self._expression(node.left), node.tag, self._expression(node.right),
                                span=node.fulltokens)
        elif node.category in set(('number', 'literal')):
            expr = VariableRef(self._constant(node), span=node.tokens)
        elif node.category == 'name':
            if node.right is None:
                expr = VariableRef(self._variable(node), span=node.tokens)
            elif node.right.tag == '(':
                expr = self._call(node)
            elif node.right.tag == '[':
                expr = self._getindex(node)
        elif node.category == 'dot':
            expr = self._getattrib(node)
        else:
            warn('Unhandled expression node: %r' % node)
        return expr

    def _constant(self, node):  #pylint: disable=R0201
        '''Handles constant nodes.'''
        assert node.category in set(('number', 'literal')), repr(node)

        if node.category == 'number':
            value = node.text
            try:
                value = float(value)
            except (ValueError, TypeError):
                pass
        else:
            value = { 'True': True, 'False': False, 'Null': None }[node.tag]
        return Variable(value=value, constant=True, span=node.tokens)

    def _variable(self, node):
        '''Handles variable nodes.'''
        assert node.category in set(('name',)), repr(node)
        assert node.right is None, repr(node.right)
        name = node.text.lower()

        var = self.variables.get(name) or self.externals.get(name)
        if not var:
            var = self.variables[name] = Variable(name=name, span=node.tokens)
        return var
        
    def _call(self, node):
        '''Handles function call nodes.'''
        assert node.category in set(('name', 'dot')), repr(node)
        
        if node.category == 'name':
            name = node.text.lower()
            func = self.externals.get(name)
        else:
            func = self._getattrib(node)

        if not func:
            func = self.externals[name] = Variable(name=name, external=True, span=node.tokens)
        
        return self._call_internal(VariableRef(func, span=node.tokens), node.right, span=node.fulltokens)

    def _call_internal(self, func, param_node, span):
        '''Internal handling for function calls.'''
        assert isinstance(func, VariableRef), repr(func)   
        if param_node is not None and param_node.tag == '(':
            func_call = Function.call(func, {}, span=span)
            if param_node.expr:
                params = []
                for p_node in param_node.expr[0].iter_list():
                    if p_node.tag == '=':
                        name = p_node.left.tag
                        value = self._expression(p_node.right)
                    else:
                        name = p_node.tag
                        value = None
                    params.append(Parameter((name, value), span=p_node.tokens))
                func_call.parameters.update(params)
        elif func.id.tag == 'function':
            func_call = func.id
        else:
            func_call = Function.call(func, {}, span=span)
        
        return func_call

    def _getindex(self, node, index_node=None):
        '''Handles indexing nodes.'''
        assert node.category in set(('name',)), repr(node)
        if index_node is None: index_node = node.right
        assert index_node is not None, repr(node)
        assert index_node.tag == '[' and len(index_node.expr) <= 1, repr(index_node)
        name = node.text.lower()

        source = self.variables.get(name) or self.externals.get(name)
        if not source:
            source = self.variables[name] = Variable(name=name, external=True, span=node.tokens)
        source = VariableRef(source, span=node.tokens)
        
        return self._getindex_internal(source, node.right, span=node.fulltokens)

    def _getindex_internal(self, source, index_node, span):
        '''Internal handling for getindex nodes.'''
        assert isinstance(source, (Function, VariableRef)), repr(source)
        
        if index_node and index_node.expr:
            index = self._expression(index_node.expr[0])
        else:
            index = None
        
        return Function.getindex(source, index, span=span)


    def _getattrib(self, node):
        '''Handles dotted attribute access nodes.'''
        assert node.category in set(('dot',)), repr(node)
        assert node.left is not None, repr(node)
        assert node.right is not None, repr(node)
        assert node.right.category == 'name', repr(node.right)
        
        source = self._expression(node.left)
        if isinstance(source, Function):
            source = VariableRef(source, span=node.left.tokens)
        assert isinstance(source, VariableRef), repr(source)

        attrib = node.right.tag.lower()
        stmt = Function.getattrib(source, attrib, node.fulltokens)
        nrr = node.right.right
        if nrr is None:
            return stmt
        elif nrr.tag == '(':
            span = node.fulltokens
            return self._call_internal(VariableRef(stmt, span=span), nrr, span)
        elif nrr.tag == '[':
            span = node.fulltokens
            return self._getindex_internal(VariableRef(stmt, span=span), nrr, span)
        else:
            warn("Unhandled dotted node child: %s (%r)" % (node, node))

    def _group(self, node):
        '''Handles group name nodes.'''
        assert node.category in set(('name',)), repr(node)
        if node.right is not None and node.right.tag == '(':
            return self._call(node)
        
        var = self._variable(node)
        return var if not var.external else self._call(node)

    def _groupref(self, node, limit=None):
        '''Handles group references, potentially included a size limit.
        Generators are also handled.
        '''
        group = self._group(node)
        if isinstance(group, Function):
            return group
        elif limit:
            return GroupRef(group, limit=self._expression(limit), span=node.fulltokens)
        else:
            return GroupRef(group, limit=None, span=node.fulltokens)

    def _fromstmt(self, node, from_cmd='FromStmt', select_cmd='SelectStmt', merge_op=Merge):
        '''Handles FROM-SELECT statements.'''
        assert node.category in set(('UsingStmt', select_cmd)), repr(node)
        
        if node.category == 'UsingStmt':
            operators = [self._call(i) for i in node.right.iter_list()]
            node = node.left
        else:
            operators = []

        assert node.category == select_cmd, repr(node)

        dests = [self._groupref(group, limit) for limit, group in node.data]
        node = node.left

        assert node.category == from_cmd, repr(node)

        srcs = [self._groupref(group, limit) for limit, group in node.data]

        gen = merge_op(srcs)
        for op in operators:
            gen = Operator(gen, op)
        gen = Store(gen, dests)
        return gen

    def _joinstmt(self, node):
        '''Handles JOIN-INTO statements.'''
        return self._fromstmt(node, from_cmd='JoinStmt', select_cmd='IntoStmt', merge_op=Join)
    
    def _evalstmt(self, node):
        '''Handles EVAL statements.'''
        assert node.category in set(('UsingStmt', 'EvalStmt')), repr(node)

        evaluators = []
        if node.category == 'UsingStmt':
            for i in node.right.iter_list():
                if i.rightmost.category == 'expr':
                    evaluators.append(self._call(i))
                else:
                    evaluators.append(self._expression(i))
            node = node.left

        assert node.category == 'EvalStmt', repr(node)

        srcs = [self._groupref(group) for _, group in node.data]

        assert len(evaluators) == 1, "Only single evaluators are supported"

        return EvalStmt(srcs, evaluators)

    def _yieldstmt(self, node):
        '''Handles YIELD statements.'''
        assert node.category == 'YieldStmt', repr(node)

        srcs = [self._groupref(group) for _, group in node.data]
        return YieldStmt(srcs)
