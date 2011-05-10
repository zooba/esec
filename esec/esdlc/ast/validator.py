'''Provides the `Analyser` class for producing a more complete model of
the provided AST.
'''
# Disable too many return statements warnings
#pylint: disable=R0911

import re
import warnings

import esdlc.errors as error

class Validator(object):
    '''Validates node-specific elements of an AST and updates `data`
    members to contain useful information.
    '''
    
    def __init__(self):
        self.errors = []

    def validate(self, stmt):
        '''Analyses the provided statement.
        
        :Parameters:
          stmt : `esdlc.ast.nodes.Node`
            A node within a syntax tree. This node or its children may
            be modified by this process.
        '''
        if stmt is None: return True

        result = True
        if stmt.category in {'block', 'expr'}:
            for node in (stmt.expr or []):
                self.validate(node)
        elif stmt.category in {'FromStmt', 'JoinStmt'}:
            result &= getattr(self, '_validate_' + stmt.category)(stmt)
            result &= self._update_groups(stmt, allow_function=True)
        elif stmt.category in {'SelectStmt', 'IntoStmt'}:
            result &= getattr(self, '_validate_' + stmt.category)(stmt)
            result &= self._update_groups(stmt, allow_size=True, repeats_error=error.RepeatedDestinationGroupError)
        elif stmt.category == 'UsingStmt':
            result &= self._validate_UsingStmt(stmt)
            result &= self._update_functions(stmt)
        elif stmt.category in {'EvalStmt', 'YieldStmt'}:
            result &= getattr(self, '_validate_' + stmt.category)(stmt)
            result &= self._update_groups(stmt, repeats_error=error.RepeatedGroupError)
        elif stmt.category in {'assign', 'name', 'dot', 'comma', 'op'}:
            result &= getattr(self, '_validate_' + stmt.category)(stmt)
        elif stmt.category in {'pragma'}:
            pass
        else:
            warnings.warn("Unhandled statement type: %s" % stmt.category)
        return result
    
    # =================================================================
    # Data Parsing

    def _update_groups(self, expr, allow_size=False, allow_function=False, repeats_error=None): #pylint: disable=R0912
        '''Reads the groups contained in ``expr.right`` and assigns
        them to ``expr.data``.
        '''
        expr.data = []
        seen_any = False
        seen_unsized = False
        errors = []
        for node in expr.right.iter_list():
            size_node = node.clone_detach()
            name_node = size_node.rightmost
            
            if name_node.category == 'expr':
                name_node = name_node.parent or size_node
            
            if name_node.category == 'name':
                while name_node.parent and name_node.parent.category == 'dot':
                    name_node = name_node.parent
            
            if size_node == name_node:
                size_node = None
            else:
                name_node.detach()
            
            if name_node is None:
                errors.append(error.ExpectedGroupError(node.fulltokens))
            elif size_node is not None and size_node.rightmost.category not in {'expr', 'name', 'number'}:
                errors.append(error.InvalidGroupError(size_node.fulltokens))
                seen_any = True
            elif size_node is not None and allow_size == False:
                errors.append(error.UnexpectedGroupSizeError(size_node.fulltokens, name_node.text))
                seen_any = True
            elif name_node.rightmost.tag == '(' and allow_function == False:
                if name_node.rightmost.parent.category == 'name':
                    errors.append(error.GeneratorAsDestinationError(name_node.fulltokens))
                else:
                    errors.append(error.InvalidGroupError(name_node.rightmost.fulltokens))
                seen_any = True
            elif name_node.category not in {'name', 'dot'}:
                errors.append(error.InvalidGroupError(name_node.tokens, name_node.text))
                seen_any = True
            else:
                if repeats_error is not None and any(i.text == name_node.text for _, i in expr.data):
                    errors.append(repeats_error(name_node.fulltokens, name_node.text))
                if size_node is not None:
                    if size_node.category == 'expr':
                        if len(size_node.expr) != 1 or size_node.expr[0].category == 'comma':
                            errors.append(error.InvalidGroupSizeError(node.tokens, name_node.text))
                expr.data.append((size_node, name_node))

            if seen_unsized and name_node:
                errors.append(error.InaccessibleGroupError(name_node.fulltokens, name_node.text))
            if allow_size and size_node is None:
                seen_unsized = True

        if not expr.data and not seen_any:
            errors.append(error.ExpectedGroupError((expr.right or expr).tokens))

        self.errors.extend(errors)
        if any(not i.iswarning for i in errors):
            return False
        return True
        
    def _update_functions(self, expr):
        '''Reads the functions contained in ``expr.right`` and assigns
        them to ``expr.data``.
        '''
        return self._update_groups(expr, allow_size=False, allow_function=True)


    # =================================================================
    # Statement Validation

    def _validate_FromStmt(self, node):
        '''Validates a FromStmt node.'''
        if node.parent is None:
            self.errors.append(error.ExpectedSelectError((node.right.right or node.right).tokens))
            return False
        elif node.parent.category != 'SelectStmt':
            self.errors.append(error.ExpectedSelectError(node.parent.tokens))
            return False
        elif node.right is None:
            self.errors.append(error.ExpectedGroupError(node.fulltokens))
            return False
        
        return True

    def _validate_SelectStmt(self, node):
        '''Validates a SelectStmt node.'''
        if node.parent is not None and node.parent.category not in {'block', 'UsingStmt'}:
            self.errors.append(error.InvalidSyntaxError(node.tokens))
            return False
        elif node.left is None or node.left.category != 'FromStmt':
            self.errors.append(error.InvalidSyntaxError((node.left or node).tokens))
            return False
        
        if not self.validate(node.left):
            return False

        if node.right is None:
            self.errors.append(error.ExpectedGroupError(node.tokens))
            return False
        
        return True

    def _validate_JoinStmt(self, node):
        '''Validates a JoinStmt node.'''
        if node.parent is None:
            self.errors.append(error.ExpectedIntoError((node.right.right or node.right).tokens))
            return False
        elif node.parent.category != 'IntoStmt':
            self.errors.append(error.ExpectedIntoError(node.parent.tokens))
            return False
        elif node.right is None:
            self.errors.append(error.ExpectedGroupError(node.tokens))
            return False
        
        return True

    def _validate_IntoStmt(self, node):
        '''Validates an IntoStmt node.'''
        if node.parent is not None and node.parent.category not in {'block', 'UsingStmt'}:
            self.errors.append(error.InvalidSyntaxError(node.tokens))
            return False
        elif node.left is None or node.left.category != 'JoinStmt':
            self.errors.append(error.InvalidSyntaxError((node.left or node).tokens))
            return False
        
        if not self.validate(node.left):
            return False

        if node.right is None:
            self.errors.append(error.ExpectedGroupError(node.tokens))
            return False
        
        return True
    
    def _validate_UsingStmt(self, node):
        '''Validates a UsingStmt node.'''
        if node.left is None or node.left.category not in {'SelectStmt', 'IntoStmt', 'EvalStmt'}:
            self.errors.append(error.InvalidSyntaxError((node.left or node).fulltokens))
            return False

        return self.validate(node.left)

    def _validate_EvalStmt(self, node):
        '''Validates an EvalStmt node.'''
        if node.parent is not None and node.parent.category not in {'block', 'UsingStmt'}:
            self.errors.append(error.InvalidSyntaxError(node.fulltokens))
            return False
        elif node.right is None:
            self.errors.append(error.ExpectedGroupError(node.fulltokens))
            return False

        return True

    def _validate_YieldStmt(self, node):
        '''Validates an YieldStmt node.'''
        if node.parent is not None and node.parent.category not in {'block'}:
            self.errors.append(error.InvalidSyntaxError(node.fulltokens))
            return False
        elif node.right is None:
            self.errors.append(error.ExpectedGroupError(node.fulltokens))
            return False

        return True
    
    # =================================================================
    # Node Validation

    def _validate_dot(self, node):
        '''Validates a dot node.'''
        return self._validate_name(node)

    def _validate_name(self, node):
        '''Validates a name node.'''
        if node is None:
            return False
        elif node.category == 'dot':
            part1 = self._validate_name(node.left)
            part2 = self._validate_name(node.right)
            return part1 and part2
        elif node.category != 'name':
            return False
        elif node.tag.startswith('_'):
            self.errors.append(error.InternalVariableNameError(node.fulltokens, node.text))
            return True
        elif not re.match('^(?!\d)\w+$', node.tag, re.IGNORECASE):
            self.errors.append(error.InvalidVariableError(node.fulltokens, node.text))
            return False
        elif node.right is not None and node.right.category == 'expr':
            return self.validate(node.right)
        return True

    def _validate_assign(self, node):
        '''Validates an assignment.'''
        name = node.left
        if name.category == 'name':
            if name.right is not None:
                self.errors.append(error.InvalidAssignmentError(name.fulltokens))
                return False
        
        elif name.category == 'dot':
            rightmost = name.rightmost
            if rightmost is None or rightmost.category != 'name':
                self.errors.append(error.InvalidAssignmentError(name.fulltokens))
                return False
        
        return self._validate_op(node.right)

    def _validate_comma(self, node):
        '''Validates a comma separated list.'''
        if node.left is None:
            self.errors.append(error.InvalidSyntaxError(node.tokens))
            return False
        if node.right is None and node.parent and node.parent.category == 'comma':
            self.errors.append(error.InvalidSyntaxError(node.tokens))
            return False
        result1 = self._validate_op(node.left)
        result2 = self._validate_op(node.right)
        return result1 and result2

    def _validate_op(self, node):
        '''Validates an arithmetic expression tree.'''
        if node is None:
            return True
        elif node.category == 'assign':
            return self._validate_assign(node)
        elif node.category in {'name', 'dot'}:
            return self._validate_name(node)
        elif node.category == 'comma':
            return self._validate_comma(node)
        elif node.category in {'op'}:
            if node.tag in "*/^%" and node.left is None:
                self.errors.append(error.InvalidSyntaxError(node.fulltokens))
                return False
            if node.tag in "+-*/^%" and node.right is None:
                self.errors.append(error.InvalidSyntaxError(node.fulltokens))
                return False
            
            result1 = self._validate_op(node.left)
            result2 = self._validate_op(node.right)
            return result1 and result2
        else:
            return True