import collections
import itertools
import esdlc.errors as error
from esdlc.model import System
from esdlc.model.components import *

Token = collections.namedtuple('Token', 'line col value')

def run_check(system_cls, expected_errors, expected_warnings):
    system = system_cls()
    validation = system.validate()
    try:
        success = False
        for expected, actual in itertools.izip_longest(expected_errors, validation.errors):
            assert expected is not None, "Expected None, Actual = %s" % (actual)
            assert actual is not None, "Expected %s, Actual = None" % (expected)
            assert isinstance(actual, expected), "Expected %s, Actual = %s" % (expected, actual)
        for expected, actual in itertools.izip_longest(expected_warnings, validation.warnings):
            assert expected is not None, "Expected None, Actual = %s" % (actual)
            assert actual is not None, "Expected %s, Actual = None" % (expected)
            assert isinstance(actual, expected), "Expected %s, Actual = %s" % (expected, actual)
        success = True
    finally:
        if not success:
            print 'Errors:\n  ' + '\n  '.join(str(i) for i in validation.errors)
            print 'Warnings:\n  ' + '\n  '.join(str(i) for i in validation.warnings)

all_tests = []
def check(cls):
    all_tests.append((run_check,
        cls, 
        [i for i in cls.EXPECT if not i.code.startswith('W')],
        [i for i in cls.EXPECT if     i.code.startswith('W')]))

def test_all():
    return all_tests

@check
class Test_UninitialisedGlobalError(System):
    EXPECT = [error.UninitialisedGlobalError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []
        
        func = Variable("func", external=True)
        statements.append(Function.call(func, {}))

@check
class Test_RepeatedParameterNameError(System):
    EXPECT = [error.RepeatedParameterNameError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []
        
        func = Variable("func", external=True)
        self.externals[func.name] = func
        func_call = Function.call(func, { 'k': Variable(value=2, constant=True) })
        func_call.parameters.update([Parameter(('k', Variable(value=5, constant=True)))])
        statements.append(func_call)

@check
class Test_AmbiguousGroupGeneratorNameError(System):
    EXPECT = [error.AmbiguousGroupGeneratorNameError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        self.variables['pop'] = Variable('pop')
        self.variables['test'] = Variable('test')
        self.externals['test'] = Variable('test', external=True)

        stmt = Merge([GroupRef(self.variables['test']), Function.call(self.externals['test'], { })])
        stmt = Store(stmt, [GroupRef(self.variables['pop'])])
        
        statements.append(stmt)

@check
class Test_AmbiguousVariableBlockNameError(System):
    EXPECT = [error.AmbiguousVariableBlockNameError, error.AmbiguousVariableBlockNameError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        self.variables['gen1'] = Variable('gen1')
        self.variables['gen2'] = Variable('gen2')
        
        stmt = Merge([GroupRef(self.variables['gen1'])])
        stmt = Store(stmt, [GroupRef(self.variables['gen1'])])
        
        statements.append(stmt)

        statements = self.blocks['gen1'] = []
        self.block_names.append('gen1')

        stmt = Function.assign(self.variables['gen2'], self.variables['gen2'])
        statements.append(stmt)

        self.blocks['gen2'] = []

@check
class Test_ExpectedGroupError(System):
    EXPECT = [error.ExpectedGroupError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        self.variables['pop'] = Variable('pop')
        self.variables['var'] = Variable('var')
        
        stmt = Merge([GroupRef(self.variables['pop'])])
        stmt = Store(stmt, [self.variables['var']])
        
        statements.append(stmt)

@check
class Test_GeneratorAsDestinationError(System):
    EXPECT = [error.GeneratorAsDestinationError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        self.variables['pop'] = Variable('pop')
        self.externals['generator'] = Variable('generator', external=True)
        
        stmt = Merge([GroupRef(self.variables['pop'])])
        stmt = Store(stmt, [Function.call(self.externals['generator'], {})])
        
        statements.append(stmt)

@check
class Test_InaccessibleGroupError(System):
    EXPECT = [error.InaccessibleGroupError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        self.variables['pop1'] = Variable('pop1')
        self.variables['pop2'] = Variable('pop2')
        self.externals['generator'] = Variable('generator', external=True)
        
        stmt = Merge([GroupRef(self.variables['pop1'])])
        stmt = Store(stmt, [GroupRef(self.variables['pop1']), GroupRef(self.variables['pop2'])])
        
        statements.append(stmt)

@check
class Test_InternalVariableNameError(System):
    EXPECT = [error.InternalVariableNameError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        self.externals['func'] = Variable('func', external=True)
        self.variables['_test'] = Variable('_test')

        stmt = Function.call(self.externals['func'], { 'test': self.variables['_test'] })
        
        statements.append(stmt)

@check
class Test_InternalParameterNameError(System):
    EXPECT = [error.InternalParameterNameError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        self.externals['func'] = Variable('func', external=True)
        self.variables['test'] = Variable('test')

        stmt = Function.call(self.externals['func'], { '_test': self.variables['test'] })
        
        statements.append(stmt)

@check
class Test_InvalidAssignmentError(System):
    EXPECT = [error.InvalidAssignmentError, error.InvalidAssignmentError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        self.externals['func'] = Variable('func', external=True)
        self.variables['test'] = Variable('test')
        c1 = Variable(value=1.0, constant=True)

        stmt = Function.assign(self.externals['func'], c1, span=Token(1, 1, ''))
        statements.append(stmt)
        stmt = Function.assign(c1, self.variables['test'], span=Token(2, 1, ''))
        statements.append(stmt)
        stmt = Function.assign(self.variables['test'], c1, span=Token(3, 1, ''))
        statements.append(stmt)
        stmt = Function.assign(self.variables['test'], self.externals['func'], span=Token(4, 1, ''))
        statements.append(stmt)

@check
class Test_InvalidGroupSizeError(System):
    EXPECT = [error.InvalidGroupSizeError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        self.externals['func'] = Variable('func', external=True)
        self.variables['pop'] = Variable('pop')
        
        src = Merge([Function.call(self.externals['func'], {})])
        stmt = Store(src, [GroupRef(self.variables['pop'], limit=self.variables['pop'])])
        
        statements.append(stmt)

@check
class Test_RepeatedGroupError(System):
    EXPECT = [error.RepeatedGroupError, error.RepeatedGroupError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        pop = self.variables['pop'] = Variable('pop')
        
        stmt = YieldStmt([GroupRef(pop, span=Token(1, 5, '')), GroupRef(pop, span=Token(1, 10, ''))])
        statements.append(stmt)
        stmt = EvalStmt([GroupRef(pop, span=Token(2, 5, '')), GroupRef(pop, span=Token(2, 10, ''))], None)
        statements.append(stmt)

@check
class Test_RepeatedDestinationGroupError(System):
    EXPECT = [error.RepeatedDestinationGroupError, error.RepeatedDestinationGroupError]

    def __init__(self):
        System.__init__(self)
        statements = self.blocks[self.INIT_BLOCK_NAME] = []

        pop = self.variables['pop'] = Variable('pop')
        n = self.variables['n'] = Variable(10, constant=True)
        
        stmt = Store(Merge([GroupRef(pop)]),
                     [GroupRef(pop, limit=n, span=Token(1, 10, '')), GroupRef(pop, span=Token(1, 15, ''))])
        statements.append(stmt)

        stmt = Store(Join([GroupRef(pop), GroupRef(pop)]),
                     [GroupRef(pop, limit=n, span=Token(2, 10, '')), GroupRef(pop, span=Token(2, 15, ''))])
        statements.append(stmt)
