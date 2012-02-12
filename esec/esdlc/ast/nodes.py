'''Contains the `Node` class and the `DEFAULT_SYMBOLS` dictionary that
are used to build abstract syntax trees for ESDL systems.
'''
from copy import copy
import itertools
import esdlc.errors as error

SHOW_REFERENCES = False

class Node(object):
    '''Represents a raw node in an AST.
    '''
    def __init__(self, tag='', *args, **kwargs):
        self.tag = tag
        assert tag is None or isinstance(tag, str), repr(tag)

        self.args = (tag,) + tuple(args)
        self.tokens = kwargs.get('tokens', [])
    
    @property
    def text(self):
        '''Returns the original text making up this node.'''
        return ''.join(t.value for t in self.tokens)

    def __getitem__(self, key):
        return self.args[key]
        
    def __len__(self):
        return len(self.args)
    
    @property
    def left(self):
        if len(self.args) >= 2:
            return self.args[1]
        else:
            return None

    @property
    def right(self):
        if len(self.args) >= 3:
            return self.args[2]
        else:
            return None

    @staticmethod
    def _format_list(source, target_list, raw=False):
        do_pop = False
        for item in source:
            if item is None:
                pass
            elif isinstance(item, Node):
                item.format(target_list, raw)
            elif isinstance(item, list):
                if item:
                    target_list.append('[')
                    Node._format_list(item, target_list, raw)
                    target_list.append(']')
            else:
                target_list.append(str(item))
            target_list.append(',')
            do_pop = True

        if do_pop:
            target_list.pop()

        return target_list

    def format(self, target_list, raw=False):
        if not raw and self.tag == 'Name':
            target_list.append(str(self.args[1]))
        elif not raw and self.tag == 'Number':
            target_list.append(str(self.args[1]))
        elif not raw and self.tag == 'Constant':
            target_list.append('Constant{%s}' % (self.args[1] if self.args[1] is not None else 'None'))
        elif not raw and self.tag == 'ParameterList':
            if self.args[1]:
                target_list.append('[')
                Node._format_list(self.args[1], target_list, raw)
                target_list.append(']')
        elif not raw and self.tag == 'Parameter':
            target_list.append('%s{%s}' % (self.args[1], self.args[2] or ''))
        else:
            target_list.extend((self.tag, '{'))
            Node._format_list(self.args[1:], target_list, raw)
            target_list.append('}')

        if raw:
            loc = self.location()
            target_list.append('<%s,%s>' % (loc[0] or '?', loc[1] or '?'))

        return target_list

    def __str__(self):
        result = []
        self.format(result)
        return ''.join(result)
    
    def __repr__(self):
        result = []
        self.format(result, raw=True)
        return ''.join(result)
    
    def location(self):
        '''Returns the start location of this node in the original
        source code.
        '''
        if self.tokens:
            return self.tokens[0].line + 1, self.tokens[0].col + 1
        else:
            return None, None
    
    def __eq__(self, other):
        try:
            return self.tag == other.tag and self.location() == other.location()
        except AttributeError:
            return False
    
