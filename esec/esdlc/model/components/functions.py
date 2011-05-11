'''Provides the `Function` object for the semantic model.
'''

__all__ = ['Function']

from esdlc.model.components.variables import Parameter
from esdlc.model.components.lists import ParameterList

class Function(object):
    '''Represents a function call. Most function calls should be
    instantiated by one of the `call`, `getattrib`, `getindex` or
    `assign` methods.
    '''
    tag = 'function'

    @classmethod
    def call(cls, source, parameter_dict, span=None):
        '''Instantiates a function call.
        '''
        inst = Function("_call", span)
        inst.parameters = ParameterList.from_args(_function=source)
        inst.parameters.update(Parameter(i) for i in parameter_dict.iteritems())
        return inst

    @classmethod
    def getattrib(cls, source, attribute, span=None):
        '''Instantiates an named attribute access.
        '''
        inst = Function("_getattrib", span)
        inst.parameters = ParameterList.from_args(_source=source, _attrib=attribute)
        return inst

    @classmethod
    def getindex(cls, source, index, span=None):
        '''Instantiates a number index access.
        '''
        inst = Function("_getindex", span)
        inst.parameters = ParameterList.from_args(_source=source, _index=index)
        return inst

    @classmethod
    def assign(cls, destination, source, span=None):
        '''Instantiates a variable assignment.
        '''
        inst = Function("_assign", span)
        inst.parameters = ParameterList.from_args(_source=source, _destination=destination)
        return inst

    def __init__(self, name, span=None):
        self.name = name
        '''The name of this function. This should be one of
        ``'_call'``, ``'_assign'``, ``'_getattrib'`` or
        ``'_getindex'``.
        '''
        self.parameters = None
        '''The list of parameters to pass to the function.'''
        self.span = span
        '''A list of tokens constituting this function call.'''
        self.references = []
        '''A list of references to this function call. In general,
        there should be no more than one reference to each call.
        '''
    
    @property
    def parameter_dict(self):
        '''A dictionary containing the parameters to this function.'''
        return dict(self.parameters)
    
    def __str__(self):
        if self.name == '_call':
            src = next(str(i.value) for i in self.parameters if i.name == '_function')
            args = ', '.join(str(i) for i in self.parameters if i.name != '_function')
            return '%s(%s)' % (src, args)
        elif self.name == '_assign':
            return '%(_destination)s = %(_source)s' % self.parameter_dict
        elif self.name == '_getattrib':
            return '%(_source)s.%(_attrib)s' % self.parameter_dict
        elif self.name == '_getindex':
            return '%(_source)s[%(_index)s]' % self.parameter_dict
        else:
            return '%s(%s)' % (self.name, self.parameters or '')

    def execute(self, context, **more_parameters):
        '''Executes this function call in the provided `context`.'''
        if self.name == '_call':
            args = dict(self.parameters.execute(context))
            args.update(more_parameters)
            src = args.pop('_function')
            return src(**args)
        elif self.name == '_assign':
            args = self.parameter_dict
            dest = args['_destination'].id
            if dest.constant or dest.external:
                raise TypeError("Cannot assign to '%s'" % dest.name)
            src = args['_source'].execute(context)
            context[dest.name] = src
        elif self.name == '_getattrib':
            args = self.parameter_dict
            src = args['_source'].execute(context)
            return getattr(src, args['_attrib'])
        elif self.name == '_getindex':
            args = dict(self.parameters.execute(context))
            src = args.pop('_source')
            return src[int(args['_index'])]
        else:
            return globals()[self.name](**dict(self.parameters.execute(context)))
