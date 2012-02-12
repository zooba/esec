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
    def __init__(self, source_file=None, ast=None, externals=None):
        super(AstSystem, self).__init__(source_file)
        self.ast = None    
        self._active = None
        
        if externals is not None:
            self.externals.update((name, Variable(name=name, value=value, external=True))
                                  for name, value in externals.iteritems())
        if ast is not None:
            self.read(ast)
            self._errors.extend(ast._errors)
        
    def read(self, ast):
        '''Reads an abstract syntax tree into the model.

        This function may be called once only for each instance of
        `AstSystem`; otherwise a ``RuntimeError`` is raised.
        '''
        if self.ast is not None:
            raise RuntimeError("Cannot call AstSystem.read() multiple times.")
        #if ast.errors:
        #    raise ValueError("AST contains errors.")
        self.ast = ast

        block_stack = []
        block = []
        self.block_names.append(self.INIT_BLOCK_NAME)
        blocks = {self.INIT_BLOCK_NAME: block}
        nesting = 0

        for stmt in ast.expr:
            if stmt is None or len(stmt) == 0:
                pass
            elif stmt[0] == 'BeginStmt' and not block_stack:
                block = []
                self.block_names.append(stmt[1])
                blocks[stmt[1]] = block
                block_stack.append(None)
            elif stmt[0] == 'RepeatStmt':
                block_stack.append(block)
                new_block = []
                block.append(type(stmt)(stmt[0], stmt[1], new_block))
                block = new_block
            elif stmt[0] == 'EndStmt':
                block = block_stack.pop()
            elif block is not None:
                block.append(stmt)
        
        for block_name in self.block_names:
            self._active = self.blocks[block_name] = []
            self._visit_block(blocks[block_name])

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
        count_expr = self._expression(block[1])
        previous = self._active
        self._active = stmts = []
        self._visit_block(block[2])
        self._active = previous
        return RepeatBlock(stmts, count_expr)

    def _visit_stmt(self, stmt):
        '''Dispatches control to the appropriate handler for `stmt`.'''
        tag = stmt[0]
        if tag == 'Comment':
            pass
        elif tag == '=':
            self._add(self._assignment(stmt))
        elif tag == 'CallFunc':
            self._add(self._call(stmt))
        elif tag == 'FromStmt':
            self._add(self._fromstmt(stmt))
        elif tag == 'JoinStmt':
            self._add(self._joinstmt(stmt))
        elif tag == 'EvalStmt':
            self._add(self._evalstmt(stmt))
        elif tag == 'YieldStmt':
            self._add(self._yieldstmt(stmt))
        elif tag == 'RepeatStmt':
            self._add(self._repeatblock(stmt))
        elif tag == 'PragmaStmt':
            self._add(Pragma(stmt[1], stmt.tokens))
        elif tag == 'Name':
            pass
        else:
            warn('Unhandled statement type: %r' % stmt)

    def _assignment(self, node):
        '''Handles assignment nodes.'''
        return Function.assign(self._expression(node.left), self._expression(node.right), node.tokens)

    def _expression(self, node):
        '''Handles expression nodes.'''
        expr = None
        if node is None:
            return None
        elif node.tag in frozenset('+-*/%^,'):
            if node.left is None:
                expr = UnaryOp(node.tag, self._expression(node.right), span=node.tokens)
            else:
                expr = BinaryOp(self._expression(node.left), node.tag, self._expression(node.right),
                                span=node.tokens)
        elif node.tag in frozenset(('Number', 'Constant')):
            expr = self._constant(node)
        elif node.tag == 'Name':
            expr = self._variable(node)
        elif node.tag == 'CallFunc':
            expr = self._call(node)
        elif node.tag == 'GetElement':
            expr = self._getindex(node)
        elif node.tag == '.':
            expr = self._getattrib(node)
        else:
            warn('Unhandled expression node: %r' % node)
        return expr

    def _constant(self, node):  #pylint: disable=R0201
        '''Handles constant nodes.'''
        assert node.tag in frozenset(('Number', 'Constant')), repr(node)

        return Variable(value=node[1], constant=True, span=node.tokens)

    def _variable(self, node):
        '''Handles variable nodes.'''
        assert node.tag == 'Name', repr(node)
        
        name = node[1]
        var = self.variables.get(name) or self.externals.get(name)
        if not var:
            var = self.variables[name] = Variable(name=name, span=node.tokens)
        return var
        
    def _call(self, node):
        '''Handles function call nodes.'''
        assert node.tag == 'CallFunc', repr(node)
        assert node[1].tag in frozenset(('Name', '.')), repr(node)

        name = None
        name_node = node[1]
        if name_node.tag == 'Name':
            name = name_node[1]
            func = self.externals.get(name)
        else:
            func = self._getattrib(name_node)

        if name and not func:
            func = self.externals[name] = Variable(name=name, external=True, span=node.tokens)
        
        return self._call_internal(func, node.right, span=node.tokens)

    def _call_internal(self, func, param_node, span):
        '''Internal handling for function calls.'''
        if param_node is not None and param_node.tag == 'ParameterList':
            func_call = Function.call(func, {}, span=span)
            if param_node[1]:
                params = []
                for p_node in param_node[1]:
                    if p_node[2]:
                        name = p_node[1]
                        value = self._expression(p_node[2])
                    else:
                        name = p_node[1]
                        value = None
                    params.append(Parameter((name, value), span=p_node.tokens))
                func_call.parameters.update(params)
        elif func.tag == 'function':
            func_call = func
        else:
            func_call = Function.call(func, {}, span=span)
        
        return func_call

    def _getindex(self, node, index_node=None):
        '''Handles indexing nodes.'''
        assert node.tag == 'GetElement', repr(node)
        name_node = node.left
        assert name_node is not None, repr(node)
        if index_node is None: index_node = node.right
        assert index_node is not None, repr(node)
        
        if name_node.tag == 'Name':
            name = name_node[1]
            source = self.variables.get(name) or self.externals.get(name)
            if not source:
                source = self.variables[name] = Variable(name=name, external=True, span=node.tokens)
        else:
            source = self._expression(name_node)
        
        return self._getindex_internal(source, node.right, span=node.tokens)

    def _getindex_internal(self, source, index_node, span):
        '''Internal handling for getindex nodes.'''
        return Function.getindex(source, self._expression(index_node), span=span)

    def _getattrib(self, node):
        '''Handles dotted attribute access nodes.'''
        assert node.tag == '.', repr(node)
        assert node.left is not None, repr(node)
        assert node.right is not None, repr(node)
        assert node.right.tag == 'Name', repr(node.right)
        
        source = self._expression(node.left)
        attrib = node.right[1]

        return Function.getattrib(source, attrib, node.tokens)

    def _group(self, node):
        '''Handles group name nodes.'''
        assert node.tag == 'Name', repr(node)
        
        var = self._variable(node)
        return var if not var.external else Function.call(var, {}, node.tokens)

    def _groupref(self, node):
        '''Handles group references, potentially included a size limit.
        Generators are also handled.
        '''
        assert node.tag in frozenset(('Group', 'CallFunc')), repr(node)

        if node.tag == 'CallFunc':
            return self._call(node)

        limit_node, group_node = node[1], node[2]
        if group_node.tag == 'Name':
            group = self._group(group_node)

        if isinstance(group, Function):
            return group
        elif limit_node:
            return GroupRef(group, limit=self._expression(limit_node), span=node.tokens)
        else:
            return GroupRef(group, limit=None, span=node.tokens)

    def _fromstmt(self, node, from_cmd='FromStmt', select_cmd='SelectStmt', merge_op=Merge):
        '''Handles FROM-SELECT statements.'''
        assert node.tag == from_cmd, repr(node)
        
        srcs = [self._groupref(group) for group in node[1]]
        dests = [self._groupref(group) for group in node[2]]
        operators = [self._call(operator) for operator in node[3]]

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
        assert node.tag == 'EvalStmt', repr(node)

        srcs = [self._groupref(group) for group in node[1]]
        evaluators = [self._call(evaluator) for evaluator in node[2]]

        return EvalStmt(srcs, evaluators)

    def _yieldstmt(self, node):
        '''Handles YIELD statements.'''
        assert node.tag == 'YieldStmt', repr(node)

        srcs = [self._groupref(group) for group in node[1]]
        return YieldStmt(srcs)
