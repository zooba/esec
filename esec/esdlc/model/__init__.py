'''Represents the semantic model of an evolutionary algorithm.
'''

import itertools
import sys
import warnings

import esdlc.errors as error
from esdlc.model.validator import Validator

__all__ = ['System', 'FluentSystem', 'AstSystem', 'Validator']

class System(object):
    '''Represents a system in the semantic model.
    '''
    INIT_BLOCK_NAME = '_init'

    def __init__(self, source_file=None):
        self.source_file = source_file
        self.variables = { }
        self.constants = [ ]
        self.externals = { }
        self.blocks = { }
        self.block_names = [ ]
        self._errors = []

    def as_esdl(self):
        '''Converts this system back to ESDL.'''
        return '\n'.join(self.as_esdl_lines())

    def as_esdl_lines(self):
        '''Converts this sytem to a list of lines of ESDL.'''
        lines = []

        def _emit(stmts, indent):
            '''Recursively writes ESDL code.'''
            for stmt in stmts:
                text = str(stmt)
                lines.append(indent + text.strip())
                if text.startswith("REPEAT "):
                    _emit(stmt.statements, indent + '    ')
                    lines.append(indent + 'END REPEAT')
        
        _emit(self.blocks[self.INIT_BLOCK_NAME], '')

        lines.append('')
        for name in self.block_names:
            if name != self.INIT_BLOCK_NAME:
                lines.append('BEGIN ' + name)
                _emit(self.blocks[name], '    ')
                lines.append('END ' + name)
            lines.append('')

        return lines

    def validate(self):
        '''Validates this model and returns an object containing lists
        of ``errors`` and ``warnings``.
        '''
        return Validator(self)

# uses System, so needs to come last
from esdlc.model.fluent import FluentSystem
from esdlc.model.astparser import AstSystem
