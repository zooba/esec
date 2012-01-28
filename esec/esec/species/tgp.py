'''Provides the `TgpSpecies` and `TgpIndividual` classes for tree-based
genetic programming (Koza-style) genomes.
'''
# Disabled: too many lines, different arguments in override,
#           too many methods, too many parameters
#pylint: disable=C0302,W0221,R0904,R0913

from copy import copy
from itertools import chain, islice, izip
import math
from esec.species import Species
from esec.individual import Individual, OnIndividual
from esec.context import rand, notify
import esec.utils

# Override Individual to provide one that keeps its valid instructions
# with it
class TgpIndividual(Individual):
    '''An `Individual` for TGP genomes. The instruction set and number
    of terminals is stored with the individual so it may be used during
    mutation operations without being respecified.
    '''
    def __init__(self, genes, parent,
                 instructions=None, instruction_set=None, terminals=2,
                 constant_bounds=None, constant_type=None, fixed_root=False,
                 statistic=None):

        '''Initialises a new `TgpIndividual`. Instances are generally
        created using the initialisation methods provided by
        `TgpSpecies`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          genes : iterable(`Instruction`, `Terminal` or `CallAdf`)
            A linear sequence of program instructions in prefix form
            (Polish notation).
          
          parent : `TgpIndividual` or `Species`
            Either the `TgpIndividual` that was used to generate the new
            individual, or an instance of `TgpSpecies`.
            
            If a `TgpIndividual` is provided, the values for
            `instructions`, `instruction_set` and `terminals` are
            taken from that.
          
          instructions : iterable(`Instruction` or `Terminal`)
            The set of instructions which may be used in the generated
            programs. It is used to allow mutation operations to
            reintroduce instructions that are missing from the current
            genome.
          
          instruction_set : string [optional]
            The name of the instruction set in use. It may be used by
            landscapes to ensure that the correct instructions are
            being used.
          
          terminals : int |ge| 0 [optional, defaults to 2]
            The number of constant values that will be provided when
            evaluating the programs.
          
          constant_bounds : tuple [optional]
            The lower (inclusive) and higher (exclusive) bounds to use
            when creating new constants. If omitted, new constants are
            never created.
          
          constant_type : type or function
            The type of constant values (for example, ``int`` or
            ``float``) or a function taking a single parameter and
            returning the value to use as a constant.
          
          fixed_root : bool [optional]
            ``True`` if the root of the tree is fixed and not permitted
            to change; otherwise, ``False``.
          
          statistic : dict [optional]
            A set of statistic values associated with this individual.
            These are accumulated with ``parent.statistic`` and allow
            statistics to accurately represent the population.
        '''
        self._phenome_string = None
        self.instructions = instructions
        self.instruction_set = instruction_set
        self.terminals = int(terminals or 0)
        self.constant_bounds = constant_bounds
        self.constant_type = constant_type
        self.fixed_root = fixed_root
        if isinstance(parent, TgpIndividual):
            self.instructions = parent.instructions
            self.instruction_set = parent.instruction_set
            self.terminals = parent.terminals
            self.constant_bounds = parent.constant_bounds
            self.constant_type = parent.constant_type
            self.fixed_root = parent.fixed_root
        
        super(TgpIndividual, self).__init__(genes, parent=parent, statistic=statistic)
    
    @property
    def root_program(self):
        '''Returns the root program of this individual.'''
        return self.genome[0]
    
    @property
    def phenome_string(self):
        '''Returns a string representation of the phenome of this
        individual.
        '''
        if not self._phenome_string:
            result = '\n'
            for adf, program in enumerate(self.genome):
                result += "Root:\n" if adf == 0 else ("ADF %d:\n" % adf)
                op_stack = []
                done = False
                
                for op in program:
                    if done: break
                    
                    if isinstance(op, Instruction) and op.param_count:
                        # Add a new item for this instruction
                        result += '  ' * len(op_stack) + '( ' + str(op) + '\n'
                        op_stack.append([op])   # not extend
                    else:
                        # Add this terminal/call to the topmost
                        # instruction
                        result += '  ' * len(op_stack) + str(op) + '\n'
                        if op_stack: op_stack[-1].append(op)
                        else: done = True
                    
                    # If the topmost instruction has enough parameters,
                    # evaluate it.
                    while not done and op_stack and (len(op_stack[-1]) == op_stack[-1][0].param_count + 1):
                        item = op_stack.pop()
                        result += '  ' * len(op_stack) + ')\n'
                        if op_stack:
                            op_stack[-1].append(item[0])
                        else:
                            done = True
                result += '\n'
            self._phenome_string = result
        return self._phenome_string
    
    @property
    def length_string(self):
        '''Returns a string representation of the number of nodes and
        the depth of the main program.
        '''
        if self.genome:
            return '%dn %dd' % (len(self.genome[0]), self.depth(self.genome[0]))
        else:
            return '0n 0d'

# Prevent pylint warning about missing docstring, too few public methods
#pylint: disable=C0111,R0903
class Instruction(object):
    '''Represents instruction nodes.'''
    def __init__(self, func, param_count, name, lazy=False):
        '''Initialises a new instruction.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          func : callable |rArr| ``type(params)``
            A function that combines its parameters and returns the
            result. The result is expected to be of the same type as the
            parameters.
          
          param_count : int |ge| 0
            The number of parameters expected by `func`.
          
          name : string
            The display name of the instruction. This is used for
            displaying formatted genomes.
          
          lazy : bool [default ``False``]
            ``True`` to only evaluate parameters when requested.
            
            When ``True``, parameters are passed to `func` as callables
            that evaluate and return the parameter value.
            
            When ``False``, parameter values are evaluated before
            calling `func`.
        '''
        self.func = func
        self.param_count = param_count
        self.name = name
        self.lazy = lazy
    
    def __call__(self, state, *params):
        return self.func(*params)
    
    def __str__(self):       return self.name
    def __repr__(self):      return "%s(%s)" % (self.name, ','.join('*' * self.param_count))
    def __eq__(self, other): return isinstance(other, Instruction) and other.func == self.func
    def __ne__(self, other): return not self.__eq__(other)

class InstructionWithState(Instruction):
    '''Represents instruction nodes where the first parameter of 
    ``func`` receives a state object global to the execution.
    '''
    def __call__(self, state, *params):
        return self.func(state, *params)

class DecisionInstruction(Instruction):
    '''Represents instruction nodes that select one of their parameters
    to evaluate. No parameter is evaluated before selection, and the
    results are not available prior to selection.
    
    The ``func`` function must return an index between 1 and
    ``param_count``, inclusive, identifying the sub-tree to execute.
    '''
    def __call__(self, state):
        return self.func()

class DecisionInstructionWithState(DecisionInstruction):
    '''Represents instruction nodes that select one of their parameters
    to evaluate. No parameter is evaluated before selection, and the
    results are not available prior to selection.
    
    The ``func`` function must return an index between 1 and
    ``param_count``, inclusive, identifying the sub-tree to execute.
    '''
    def __call__(self, state):
        return self.func(state)

class ListInstruction(Instruction):
    '''Represents a combining instruction that evaluates all its
    parameters in order and returns them in a list.
    '''
    def __init__(self, param_count, name):
        '''Initialises a `ListInstruction` with `param_count` elements.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          param_count : int |ge| 0
            The number of parameters to combine into a list.
          
          name : string
            The display name of the instruction. This is used for
            displaying formatted genomes.
        '''
        super(ListInstruction, self).__init__(None, param_count, name)
    
    def __call__(self, state, *params):
        '''Returns all the parameters as a list.
        '''
        return list(params)

class Terminal(object):
    '''Represents terminal nodes providing constant values.'''
    def __init__(self, index):
        '''Initialises a new terminal node. The value is determined when
        evaluating the program.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          index : int |ge| 0
            The index of the terminal to return.
        '''
        self.index = index
        self.param_count = 0
    
    def __call__(self, state, terminals):
        return terminals[self.index]
    
    def __str__(self):       return 'T%02d' % self.index
    def __repr__(self):      return "Terminal(%d)" % self.index
    def __eq__(self, other): return isinstance(other, Terminal) and other.index == self.index
    def __ne__(self, other): return not self.__eq__(other)

class CallAdf(object):
    '''Represents terminal nodes referencing the result of an ADF.'''
    def __init__(self, index):
        '''Initialises a new terminal node referencing an ADF. The
        result of the ADF is determined when evaluating the program.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          index : current ADF index < int |le| maximum ADF index
            The index of the ADF to return.
        '''
        self.index = index
        self.param_count = 0
    
    def __call__(self, state, *params):
        assert False, "CallAdf objects should not be called directly."
    
    def __str__(self):              return 'ADF%d' % self.index
    def __repr__(self):             return "CallAdf(%d)" % self.index
    def __eq__(self, other):        return isinstance(other, CallAdf) and other.index == self.index
    def __ne__(self, other):        return not self.__eq__(other)

class Constant(object):
    '''Represents constant value nodes.'''
    def __init__(self, value):
        '''Initialises a new constant node with a given value.
        
        :Parameters:
          value
            The value of the constant.
        '''
        self.value = value
        self.param_count = 0
    
    def __call__(self, state, *params):
        return self.value
    
    def __str__(self):              return str(self.value)
    def __repr__(self):             return repr(self.value)
    def __eq__(self, other):        return isinstance(other, Constant) and other.value == self.value
    def __ne__(self, other):        return not self.__eq__(other)

#pylint: enable=C0111,R0903

def _safe_exp(value):
    '''Finds the exponent of `value`, returning ``0.0`` if an overflow
    occurs.
    '''
    try: return math.exp(value)
    except OverflowError: return 0.0

class TgpSpecies(Species):
    '''Provides individuals with genomes of tree-based genetic
    programming (TGP) programs. The first gene is always the main
    program, with every other gene representing an automatically-defined
    function (ADF).
    '''
    name = 'TGP'
    
    def __init__(self, cfg, eval_default):
        super(TgpSpecies, self).__init__(cfg, eval_default)
        # Make some names public within the execution context
        self.public_context = {
            'random_tgp': self.init_tgp,
            'boolean_tgp': self.init_boolean_tgp,
            'real_tgp': self.init_real_tgp,
            'integer_tgp': self.init_integer_tgp,
            
            'mutate_permutate': OnIndividual('mutate_permutate'),
            'mutate_edit': OnIndividual('mutate_edit'),
        }
    
    def evaluate(self, indiv, state=None, terminals=None, adf_index=0,  #pylint: disable=R0912
                 i_start=0, i_end=-1):
        '''Evaluates the given individual against the specified set of
        terminals and returns the result.
        
        The type of the return value depends on the type of program
        being evaluated.
        
        :Parameters:
          indiv : `TgpIndividual`
            A particular individual to evaluate. The entire individual
            is required to allow any referenced ADFs to be evaluated.
          
          state : anything
            A caller-specified object that is passed directly to every
            `InstructionWithState` object.
          
          terminals : list/tuple
            A list of terminal values to use. Terminals are references
            by index, which is assigned when creating the programs.
          
          adf_index : int
            Specifies which ADF to evaluate. A value of zero (``0``)
            evaluates the root program.
            This parameter is used internally for `CallAdf`
            instructions.
        '''

        assert isinstance(indiv, TgpIndividual), "Expected TgpIndividual, not %s" % type(indiv)
        if terminals is None: terminals = []
        assert isinstance(terminals, (list, tuple)), "terminals must be list/tuple type"
        assert len(terminals) >= indiv.terminals, "terminals does not have enough values"
        
        op_stack = []
        
        # These are used to skip trees not evaluated due to a
        # DecisionInstruction.
        skip_1 = []  # nodes to skip before
        take_1 = []  # nodes to take during
        skip_2 = []  # nodes to skip after
        
        assert 0 <= adf_index < len(indiv.genome), \
               "ADF index %d is not valid (must be [0, %d))" % (adf_index, len(indiv.genome))
        current_program = indiv.genome[adf_index]
        
        for op_i, op in islice(enumerate(current_program), i_start, i_end if i_end > i_start else None):
            # Skip instructions if we need to
            if skip_1 and skip_1[-1]:
                skip_1[-1] -= 1
                continue
            elif take_1 and take_1[-1]:
                take_1[-1] -= 1
            elif skip_2 and skip_2[-1]:
                skip_2[-1] -= 1
                continue
            if take_1 and take_1[-1] == 0 and skip_2 and skip_2[-1] == 0:
                skip_1.pop()
                take_1.pop()
                skip_2.pop()
            
            
            if isinstance(op, DecisionInstruction):
                # Determine how many instructions to skip
                selection = op(state) - 1
                spans = [(op_i + 1, self._find_end(current_program, op_i + 1))]
                for _ in xrange(1, op.param_count):
                    start = spans[-1][1]
                    spans.append((start, self._find_end(current_program, start)))
                skip_1.append(spans[selection][0] - spans[0][0])
                take_1.append(spans[selection][1] - spans[selection][0])
                skip_2.append(spans[-1][1] - spans[selection][1])
                
            elif isinstance(op, Instruction):
                # Add a new item for this instruction
                if op.lazy:
                    item = []
                    i = op_i + 1
                    for _ in xrange(op.param_count):
                        j = self._find_end(current_program, i)
                        def make_lazy_eval(indiv, state, terminals, adf_index, i, j):
                            '''Creates an evaluation lambda.'''
                            return lambda: self.evaluate(indiv, state, terminals, adf_index, i, j)
                        item.append(make_lazy_eval(indiv, state, terminals, adf_index, i, j))
                        i = j
                    if op_stack:
                        op_stack[-1].append(op(state, *item))
                    else:
                        return op(state, *item)
                else:
                    op_stack.append([op])   # not extend
            elif isinstance(op, (Terminal, Constant)):
                # Add this terminal or constant to the topmost instruction
                val = op(state, terminals)
                if op_stack: op_stack[-1].append(val)
                else: return val
            elif isinstance(op, CallAdf):
                # Add the result of this ADF to the topmost instruction
                val = self.evaluate(indiv, state, terminals, op.index)
                if op_stack: op_stack[-1].append(val)
                else: return val
            
            # If the topmost instruction has enough parameters, evaluate it.
            while op_stack and (len(op_stack[-1]) == op_stack[-1][0].param_count + 1):
                item = op_stack.pop()
                if op_stack:
                    op_stack[-1].append(item[0](state, *item[1:]))
                else:
                    return item[0](state, *item[1:])
    
    def depth(self, program):   #pylint: disable=R0201
        '''Returns the depth of a given program.
        
        :Parameters:
          program : iterable(`Instruction`)
            The program to determine the depth of.
        
        :Returns: The depth of the deepest branch of `program`.
        '''
        assert hasattr(program, '__iter__'), "individual must be iterable type"
        
        op_stack = []
        max_depth = 1
        for op in program:
            if isinstance(op, Instruction) and op.param_count:
                # Add the parameter count for this instruction
                op_stack.append(op.param_count)
                if len(op_stack) > max_depth: max_depth = len(op_stack)
            else:
                # Add this terminal to the topmost instruction
                if op_stack: op_stack[-1] -= 1
                while op_stack and op_stack[-1] <= 0:
                    op_stack.pop()
                    if op_stack: op_stack[-1] -= 1
        return max_depth

    
    _instr_bool_and = Instruction(lambda a, b: a and b, 2, 'AND')
    _instr_bool_or  = Instruction(lambda a, b: a and b, 2, 'OR')
    _instr_bool_xor = Instruction(lambda a, b: a ^ b, 2, 'XOR')
    _instr_bool_not = Instruction(lambda a   : not a, 1, 'NOT')
    _instr_bool_if  = Instruction(lambda a, b, c: b if a else c, 3, 'IF')
    
    _instr_real_add = _instr_int_add = Instruction(lambda a, b: a + b, 2, '+')
    _instr_real_sub = _instr_int_sub = Instruction(lambda a, b: a - b, 2, '-')
    _instr_real_mul = _instr_int_mul = Instruction(lambda a, b: a * b, 2, '*')
    _instr_real_div = Instruction(lambda a, b: ((a/b) if b else 0.0), 2, '/')
    _instr_int_div  = Instruction(lambda a, b: ((a/b) if b else 0), 2, '/')
    
    _instr_trans_sin = Instruction(math.sin, 1, 'sin')
    _instr_trans_cos = Instruction(math.cos, 1, 'cos')
    _instr_trans_exp = Instruction(_safe_exp, 1, 'exp')
    _instr_trans_log = Instruction(lambda a: (math.log(abs(a)) if a else 0.0), 1, 'log')
    
    boolean_instructions = (_instr_bool_and, _instr_bool_or, _instr_bool_xor, _instr_bool_not, _instr_bool_if)
    '''The set of boolean instructions.'''
    real_instructions = (_instr_real_add, _instr_real_sub, _instr_real_mul, _instr_real_div)
    '''The set of real-valued instructions.'''
    transcendental_instructions = (_instr_trans_sin, _instr_trans_cos, _instr_trans_exp, _instr_trans_log)
    '''The set of transcendental instructions.'''
    integer_instructions = (_instr_int_add, _instr_int_sub, _instr_int_mul, _instr_int_div)
    '''The set of integer instructions.'''
    
    @classmethod
    def _init_one(cls, instructions, terminals, deepest,
                  adfs, adf_index,
                  constant_bounds, constant_type,
                  terminal_prob,
                  fixed_root):
        '''Creates a single TGP genome.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          instructions : list(`Instruction`)
            The instruction set to select instructions from.
          
          terminals : list
            The terminals that may be selected.
          
          deepest : int > 0
            The deepest tree to allow.
          
          adfs : int |ge| 0
            The number of ADFs to allow for.
          
          adf_index : int |ge| 0
            The index of the ADF being generated. References to ADFs
            with an equal or lower index are not permitted.
          
          constant_bounds : tuple or ``None``
            The lowest (inclusive) and highest (exclusive) values that a
            constant may take. If omitted, no constants are ever
            created.
          
          constant_type : type or function
            The type of constant values (for example, ``int`` or
            ``float``) or a function taking a single parameter and
            returning the value to use as a constant.
          
          terminal_prob : |prob|
            The probability of a terminal, constant or ADF call being
            selected rather than an instruction.
            
            Each terminal and ADF greater than `adf_index` has an equal
            probability of being selected, for example, if `adfs` is
            two, `adf_index` is one and `terminals` is three, there are
            2-1+3=4 alternatives, each with an equal probability.
            
            Constants are assumed to number as many as `terminals`, that
            is, if `terminals` is five, there are also 'five' constants
            that may be selected (though the value of the constant is
            determined separately). If `terminals` is zero but
            `constant_bounds` is not ``None``, there is 'one' constant
            available. If `constant_bounds` is ``None``, no constants
            are ever created.
          
          fixed_root : `Instruction` or ``None``
            The instruction that must always exist at the root of the
            tree.
        
        :Returns:
            A list containing instances of `Instruction`, `Terminal`,
            `Constant` and `CallAdf` in a prefix form (that is, each
            instruction is followed by its parameters, also known as
            Polish notation).
        '''
        assert instructions is not True, "instructions has no value"
        assert terminals is not True, "terminals has no value"
        assert deepest is not True, "deepest has no value"
        assert adfs is not True, "adfs has no value"
        assert terminal_prob is not True, "terminal_prob has no value"
        
        irand = rand.randrange
        frand = rand.random
        choice = rand.choice
        
        terminals = int(terminals or 0)
        terminal_set = [Terminal(i) for i in xrange(terminals)] + [i for i in instructions if not i.param_count]
        terminals = len(terminal_set)
        deepest = int(deepest or 0)
        adfs = int(adfs or 0)
        adf_index = int(adf_index or 0)
        constants = (terminals or 1) if constant_bounds else 0
        assert (adfs - adf_index) + terminals + constants, "No terminals available"
        
        def _rnd(depth, adf_index):
            '''Recursively creates an instruction and its parameters (if
            any).
            '''
            if (deepest is not None and depth >= deepest) or frand() < terminal_prob:
                i = irand(-adfs + adf_index, constants + terminals)
                if i < 0:
                    root = [CallAdf(-i + adf_index)]
                elif i < constants:
                    if constant_type is int:
                        # Optimise for integer case
                        root = [Constant(irand(*constant_bounds))]
                    else:
                        value = frand() * (constant_bounds[1] - constant_bounds[0]) + constant_bounds[0]
                        root = [Constant(constant_type(value))]
                else:
                    root = [copy(terminal_set[i - constants])]
            else:
                root = [copy(choice(instructions))]
                for _ in xrange(root[0].param_count):
                    root.extend(_rnd(depth + 1, adf_index))
            root[0].depth = depth
            
            return root
        
        if fixed_root:
            root = [copy(fixed_root)]
            for _ in xrange(root[0].param_count):
                root.extend(_rnd(1, adf_index))
            root[0].depth = 0
        else:
            root = _rnd(0, adf_index)
        
        return root
    
    def init_tgp(self, instructions, terminals=0, deepest=10,
                 adfs=0, 
                 lowest_int_constant=None, highest_int_constant=None,
                 lowest_constant=None, highest_constant=None,
                 terminal_prob=0.5, fixed_root=False):
        '''Creates tree-based genetic programming (TGP) programs made
        from `instructions`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          instructions : iterable(`Instruction`)
            The instruction set to select instructions from.
          
          terminals : int
            The number of externally provided constants that are
            available for inclusion in programs.
          
          deepest : int
            The maximum depth program tree that may be created. Some
            programs may be less deep than this value if they fully
            terminate before reaching this depth.
          
          adfs : int
            The number of automatically-defined functions to include.
            This amount of ADFs are always generated, but are not
            necessarily called from other ADFs or the root program.
            A root program is always created, regardless of this value.
          
          lowest_int_constant : int
            The lowest (inclusive) value of integer constant to create.
            If ``None`` or greater than `highest_constant`, constants
            are never created. This value cannot be specified with
            either `lowest_constant` or `highest_constant`.
          
          highest_int_constant : int
            The highest (inclusive) value of integer constant to create.
            If ``None`` or less than `lowest_int_constant`, constants
            are never created. This value cannot be specified with
            either `lowest_constant` or `highest_constant`.
          
          lowest_constant : float
            The lowest (inclusive) value of constant to create. If
            ``None`` or greater than `highest_constant`, constants are
            never created. This value cannot be specified with either
            `lowest_int_constant` or `highest_int_constant`.
            
            These constants are real values. To create integer constants
            specify `lowest_int_constant` and `highest_int_constant`
            instead.
          
          highest_constant : float
            The highest (exclusive) value of constant to create. If
            ``None`` or less than `lowest_constant`, constants are never
            created. This value cannot be specified with either
            `lowest_int_constant` or `highest_int_constant`.
            
            These constants are real values. To create integer constants
            specify `lowest_int_constant` and `highest_int_constant`
            instead.
          
          terminal_prob : |prob|
            The probability of a branch terminating at any particular
            point. If this is zero, the program tree will be filled to
            the depth specified by `deepest`.
          
          fixed_root : bool
            ``True`` to limit the root of all trees to be the first
            instruction in `instructions`; otherwise, ``False`` to allow
            any instruction to exist at the root.
        '''
        assert lowest_int_constant is not True, "lowest_int_constant has no value"
        assert highest_int_constant is not True, "highest_int_constant has no value"
        assert lowest_constant is not True, "lowest_constant has no value"
        assert highest_constant is not True, "highest_constant has no value"
        
        instructions = list(instructions)
        instruction_set = ''.join(instr.name for instr in instructions)
        
        assert lowest_constant is None or lowest_int_constant is None, \
            "Cannot specify both lowest_constant and lowest_int_constant."
        assert highest_constant is None or highest_int_constant is None, \
            "Cannot specify both highest_constant and highest_int_constant."
        
        if lowest_int_constant is not None:
            lowest_constant = int(lowest_int_constant)
        if highest_int_constant is not None:
            highest_constant = int(highest_int_constant)
        
        if lowest_constant is None or highest_constant is None or lowest_constant > highest_constant:
            constant_bounds = None
        else:
            constant_bounds = (lowest_constant, highest_constant)
        
        while True:
            genes = [self._init_one(instructions,
                                    terminals,
                                    deepest,
                                    adfs,
                                    i,
                                    constant_bounds,
                                    type(constant_bounds[0]) if constant_bounds else None,
                                    terminal_prob,
                                    instructions[0] if fixed_root else None)
                     for i in xrange(adfs+1)]
            yield TgpIndividual(genes,
                                self,
                                instructions,
                                instruction_set,
                                terminals,
                                constant_bounds,
                                type(constant_bounds[0]) if constant_bounds else None,
                                fixed_root)
    
    def init_boolean_tgp(self,
                         terminals=0, deepest=10,
                         adfs=0,
                         constants=False, no_constants=False,   #pylint: disable=W0613
                         terminal_prob=0.5):
        '''Creates tree-based genetic programming (TGP) programs made
        from `boolean_instructions`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          terminals : int
            The number of externally provided constants that are
            available for inclusion in programs.
          
          deepest : int
            The maximum depth program tree that may be created. Some
            programs may be less deep than this value if they fully
            terminate before reaching this depth.
          
          adfs : int
            The number of automatically-defined functions to include.
            This amount of ADFs are always generated, but are not
            necessarily called from other ADFs or the root program.
            A root program is always created, regardless of this value.
          
          constants : bool
            ``True`` to allow random constants to be included. If
            neither `constants` nor `no_constants` are specified,
            `no_constants` is the default.
          
          no_constants : bool
            ``True`` to prevent random constants to be included. This is
            the default.
          
          terminal_prob : |prob|
            The probability of a branch terminating at any particular
            point. If this is zero, the program tree will be filled to
            the depth specified by `deepest`.
        
        '''
        instructions = TgpSpecies.boolean_instructions
        instruction_set = 'boolean'
        constant_bounds = (0, 2) if constants else None
        while True:
            genes = [self._init_one(instructions,
                                    terminals,
                                    deepest,
                                    adfs,
                                    i,
                                    constant_bounds,
                                    int,
                                    terminal_prob,
                                    None)
                     for i in xrange(adfs+1)]
            yield TgpIndividual(genes,
                                self,
                                instructions,
                                instruction_set,
                                terminals,
                                constant_bounds,
                                int,
                                False)
    
    def init_real_tgp(self,
                      terminals=0, deepest=10,
                      adfs=0,
                      terminal_prob=0.5,
                      transcendentals=False,
                      lowest_constant=None, highest_constant=None):
        '''Creates tree-based genetic programming (TGP) programs made
        from `real_instructions` and, optionally,
        `transcendental_instructions`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          terminals : int
            The number of externally provided constants that are
            available for inclusion in programs.
          
          deepest : int
            The maximum depth program tree that may be created. Some
            programs may be less deep than this value if they fully
            terminate before reaching this depth.
          
          adfs : int
            The number of automatically-defined functions to include.
            This amount of ADFs are always generated, but are not
            necessarily called from other ADFs or the root program.
            A root program is always created, regardless of this value.
          
          terminal_prob : |prob|
            The probability of a branch terminating at any particular
            point. If this is zero, the program tree will be filled to
            the depth specified by `deepest`.
          
          transcendentals : bool
            ``True`` to include `transcendental_instructions`;
            otherwise, ``False``. Defaults to ``False``.
          
          lowest_constant : float
            The lowest (inclusive) value of constant to create. If
            ``None`` or greater than `highest_constant`, constants are
            never created.
          
          highest_constant : float
            The highest (exclusive) value of constant to create. If
            ``None`` or less than `lowest_constant`, constants are never
            created.
        '''
        assert lowest_constant is not True, "lowest_constant has no value"
        assert highest_constant is not True, "highest_constant has no value"
        
        instructions = TgpSpecies.real_instructions
        instruction_set = 'real'
        if lowest_constant is None or highest_constant is None or lowest_constant > highest_constant:
            constant_bounds = None
        else:
            constant_bounds = (lowest_constant, highest_constant)
        if transcendentals:
            instructions = list(TgpSpecies.real_instructions)
            instructions.extend(TgpSpecies.transcendental_instructions)
        while True:
            genes = [self._init_one(instructions,
                                    terminals,
                                    deepest,
                                    adfs,
                                    i,
                                    constant_bounds,
                                    float,
                                    terminal_prob,
                                    None)
                     for i in xrange(adfs+1)]
            yield TgpIndividual(genes,
                                self,
                                instructions,
                                instruction_set,
                                terminals,
                                constant_bounds,
                                float,
                                False)
    
    def init_integer_tgp(self,
                         terminals=0,
                         deepest=10,
                         adfs=0,
                         terminal_prob=0.5,
                        lowest_constant=None, highest_constant=None):
        '''Creates tree-based genetic programming (TGP) programs made
        from `integer_instructions`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          terminals : int
            The number of externally provided constants that are
            available for inclusion in programs.
          
          deepest : int
            The maximum depth program tree that may be created. Some
            programs may be less deep than this value if they fully
            terminate before reaching this depth.
          
          adfs : int
            The number of automatically-defined functions to include.
            This amount of ADFs are always generated, but are not
            necessarily called from other ADFs or the root program.
            A root program is always created, regardless of this value.
          
          terminal_prob : |prob|
            The probability of a branch terminating at any particular
            point. If this is zero, the program tree will be filled to
            the depth specified by `deepest`.
        
          lowest_constant : int
            The lowest (inclusive) value of constant to create. If
            ``None``, greater than or equal to `highest_constant`,
            constants are never created.
          
          highest_constant : int
            The highest (inclusive) value of constant to create. If
            ``None``, less than or equal to `lowest_constant`,
            constants are never created.
        '''
        assert lowest_constant is not True, "lowest_constant has no value"
        assert highest_constant is not True, "highest_constant has no value"
        
        instructions = TgpSpecies.integer_instructions
        instruction_set = 'integer'
        if lowest_constant is None or highest_constant is None or lowest_constant > highest_constant:
            constant_bounds = None
        else:
            constant_bounds = (int(lowest_constant), int(highest_constant) + 1)
        while True:
            genes = [self._init_one(instructions,
                                    terminals,
                                    deepest,
                                    adfs,
                                    i,
                                    constant_bounds,
                                    int,
                                    terminal_prob,
                                    None)
                     for i in xrange(adfs+1)]
            yield TgpIndividual(genes,
                                self,
                                instructions,
                                instruction_set,
                                terminals,
                                constant_bounds,
                                int,
                                False)
    
    def crossover_one(self, _source,
                      per_pair_rate=None, per_indiv_rate=1.0, per_adf_rate=1.0,
                      longest_result=None, deepest_result=None,
                      terminal_prob=None):
        '''
        :Note: This sedirects to `crossover_one_different`. Tree-based
               Genetic Programming has no sensible way in which to cross
               two individuals at the same point.
        '''
        return self.crossover_one_different(_source,
                                            per_pair_rate,
                                            per_indiv_rate,
                                            per_adf_rate,
                                            longest_result,
                                            deepest_result,
                                            terminal_prob)
    
    def crossover_one_different(self, _source,
                                per_pair_rate=None, per_indiv_rate=1.0, per_adf_rate=1.0,
                                longest_result=None, deepest_result=None,
                                terminal_prob=None):
        '''Performs single-point crossover by selecting a random program
        node in each ADF of a pair of individuals and exchanging the
        branches.
        
        ADFs are only recombined with ADFs of equivalent index to ensure
        that circular or recursive references are not introduced.
        
        Returns a sequence of crossed individuals based on the
        individuals in `_source`. The resulting sequence will contain as
        many individuals as `_source` (unless `_source` contains an odd
        number, in which case one less will be returned).
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`TgpIndividual`)
            A sequence of individuals. Individuals are taken two at a
            time from this sequence, recombined to produce two new
            individuals, and yielded separately.
          
          per_pair_rate : |prob|
            The probability of any particular pair of individuals being
            recombined. If two individuals are not recombined, they are
            returned unmodified. If this is ``None``, the value of
            `per_indiv_rate` is used.
          
          per_indiv_rate : |prob|
            A synonym for `per_pair_rate`.
          
          per_adf_rate : |prob|
            The probability of each ADF within individuals being
            recombined. If individuals are not selected for
            recombination (under `per_indiv_rate`) then no ADFs will be
            recombined. Otherwise, each ADF within the selected
            individuals is recombined with a probability of
            `per_adf_rate`.
          
          longest_result : int > 0
            A direct synonym for `deepest_result`.
          
          deepest_result : int > 0
            The deepest new program to create. If the crossover
            operation produces a deeper program or ADF then the
            offspring are discarded and the original individuals are
            returned. An ``'aborted'`` notification is sent to the
            monitor from ``'crossover_one'``.
          
          terminal_prob : |prob| [optional]
            Biases the probability of selecting a terminal as the root
            of the crossover operation. If provided, and the probability
            is met, a terminal is guaranteed to be selected. Otherwise, 
            a non-terminal is guaranteed.
            
            If omitted, the distribution of crossover points is not
            artifically biased.
        '''
        assert per_pair_rate is not True, "per_pair_rate has no value"
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_adf_rate is not True, "per_adf_rate has no value"
        assert longest_result is not True, "longest_result has no value"
        assert deepest_result is not True, "deepest_result has no value"
        assert terminal_prob is not True, "terminal_prob has no value"
        
        frand = rand.random
        
        if per_pair_rate is None: per_pair_rate = per_indiv_rate
        do_all_pairs = (per_pair_rate >= 1.0)
        do_all_adf = (per_adf_rate >= 1.0)
        
        if deepest_result is None: deepest_result = longest_result
        
        deepest_result = int(deepest_result or 0)
        
        for i1_pre, i2_pre in esec.utils.pairs(_source):
            if do_all_pairs or frand() < per_pair_rate:
                assert len(i1_pre.genome) == len(i2_pre.genome), "ADF counts are not consistent"
                i1_post = []
                i2_post = []
                
                for adf, (program1, program2) in enumerate(izip(i1_pre.genome, i2_pre.genome)):
                    new_program1 = program1
                    new_program2 = program2
                    
                    if ((do_all_adf or frand() < per_adf_rate) and
                        (len(program1) > 1 and len(program2) > 1)):
                        
                        can_select_root = (adf > 0 or not i1_pre.fixed_root)
                        start1, end1 = self._pick_random_node(program1, terminal_prob, can_select_root)
                        start2, end2 = self._pick_random_node(program2, terminal_prob, can_select_root)
                        
                        if start1 < end1 and start2 < end2:
                            new_program1 = list(chain(islice(program1, 0, start1),
                                                      islice(program2, start2, end2),
                                                      islice(program1, end1, None)))
                            new_program2 = list(chain(islice(program2, 0, start2),
                                                      islice(program1, start1, end1),
                                                      islice(program2, end2, None)))
                            
                            if (deepest_result and self.depth(new_program1) > deepest_result or 
                                deepest_result and self.depth(new_program2) > deepest_result):
                                stats = { 
                                    'i1': i1_pre,
                                    'i2': i2_pre,
                                    'adf': adf,
                                    'deepest_result': deepest_result
                                }
                                notify('crossover_one', 'aborted', stats)
                                new_program1 = program1
                                new_program2 = program2
                    
                    i1_post.append(new_program1)
                    i2_post.append(new_program2)
                
                if i1_post and i2_post:
                    yield type(i1_pre)(i1_post, i1_pre, statistic={ 'recombined': 1 })
                    yield type(i2_pre)(i2_post, i2_pre, statistic={ 'recombined': 1 })
                else:
                    yield i1_pre
                    yield i2_pre
            else:
                yield i1_pre
                yield i2_pre
    
    def mutate_random(self, _source,
                      per_indiv_rate=1.0, per_gene_rate=None, per_adf_rate=1.0,
                      deepest_result=None,
                      terminal_prob=0.5):
        '''Mutates a group of individuals by replacing branches with new
        randomly generated branches.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`TgpIndividual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an individual
            is not mutated, it is returned unmodified.
          
          per_gene_rate : |prob|
            An alias for `per_adf_rate`, included for compatibility with
            other ``mutate_random`` methods.
          
          per_adf_rate : |prob|
            The probability of each ADF within individuals being mutated.
            If individuals are not selected for mutation (under
            `per_indiv_rate`) then no ADFs will be mutated. Otherwise,
            each ADF within the selected individuals is mutated with a
            probability of `per_adf_rate`.
          
          deepest_result : int > 0 [optional]
            The deepest new program to create. The mutation operation
            limits the depth of generated branches to ensure this value is
            not exceeded. If this value is not provided, `terminal_prob` is
            the only limiting factor.
          
          terminal_prob : |prob|
            The probability of a branch terminating at any particular
            point. If this is zero, the program tree will be filled to
            the depth specified by `deepest_result`.
        '''
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_adf_rate is not True, "per_adf_rate has no value"
        assert deepest_result is not True, "deepest_result has no value"
        assert terminal_prob is not True, "terminal_prob has no value"
        
        frand = rand.random
        
        if per_gene_rate is not None: per_adf_rate = per_gene_rate
        do_all_indiv = (per_indiv_rate >= 1.0)
        do_all_adf = (per_adf_rate >= 1.0)
        
        deepest_result = int(deepest_result or 0)
        def _mutate(indiv):
            '''Returns a potentially mutated individual.'''
            assert isinstance(indiv, TgpIndividual), "Want `TgpIndividual`, not `%s`" % type(indiv)
            
            new_genes = []
            for adf, program in enumerate(indiv.genome):
                new_program = program
                
                if do_all_adf or frand() < per_adf_rate:
                    start, end = self._pick_random_node(program, allow_root=(adf > 0 or not indiv.fixed_root))
                    if start < end:
                        depth_limit = (deepest_result - self.depth(program[:start])) if deepest_result else None
                        replacement = self._init_one(indiv.instructions, indiv.terminals, depth_limit,
                                                     len(indiv.genome) - 1, adf,
                                                     indiv.constant_bounds, indiv.constant_type,
                                                     terminal_prob, False)
                        new_program = list(chain(islice(program, 0, start),
                                                 replacement,
                                                 islice(program, end, None)))
                
                new_genes.append(new_program)
            return new_genes
        
        for indiv in _source:
            if do_all_indiv or frand() < per_indiv_rate:
                yield type(indiv)(_mutate(indiv), indiv, statistic={ 'mutated': 1 })
            else:
                yield indiv
    
    def mutate_permutate(self, _source, per_indiv_rate=1.0, per_adf_rate=1.0):
        '''Mutates a group of individuals by selecting a random node and
        randomly reordering its parameters.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`TgpIndividual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an individual
            is not mutated, it is returned unmodified.
          
          per_adf_rate : |prob|
            The probability of each ADF within individuals being mutated.
            If individuals are not selected for mutation (under
            `per_indiv_rate`) then no ADFs will be mutated. Otherwise,
            each ADF within the selected individuals is mutated with a
            probability of `per_adf_rate`.
        '''
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_adf_rate is not True, "per_adf_rate has no value"
        
        frand = rand.random
        shuffle = rand.shuffle
        
        do_all_indiv = (per_indiv_rate >= 1.0)
        do_all_adf = (per_adf_rate >= 1.0)
        
        def _mutate(indiv):
            '''Returns a potentially mutated individual.'''
            assert isinstance(indiv, TgpIndividual), "Want `TgpIndividual`, not `%s`" % type(indiv)
            
            new_genes = []
            for adf, program in enumerate(indiv.genome):
                new_program = program
                
                if do_all_adf or frand() < per_adf_rate:
                    start, end = self._pick_random_node(program, allow_root=(adf > 0 or not indiv.fixed_root))
                    if start < end:
                        params = []
                        start1 = start + 1
                        for _ in xrange(program[start].param_count):
                            end1 = self._find_end(program, start1)
                            params.append(program[start1:end1])
                            start1 = end1 + 1
                        shuffle(params)
                        replacement = []
                        for param in params:
                            replacement.extend(param)
                        new_program = list(chain(islice(program, start+1),
                                                 replacement,
                                                 islice(program, end, None)))
                
                new_genes.append(new_program)
            return new_genes
        
        for indiv in _source:
            if do_all_indiv or frand() < per_indiv_rate:
                yield type(indiv)(_mutate(indiv), indiv, statistic={ 'mutated': 1, 'permutated': 1 })
            else:
                yield indiv

    
    def mutate_edit(self, _source, per_indiv_rate=1.0, per_adf_rate=1.0):
        '''Mutates a group of individuals by simplifying instruction sequences
        that are redundant or contradictory.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          _source : iterable(`TgpIndividual`)
            A sequence of individuals. Individuals are taken one at a time
            from this sequence and either returned unaltered or cloned and
            mutated.
          
          per_indiv_rate : |prob|
            The probability of any individual being mutated. If an individual
            is not mutated, it is returned unmodified.
          
          per_adf_rate : |prob|
            The probability of each ADF within individuals being mutated.
            If individuals are not selected for mutation (under
            `per_indiv_rate`) then no ADFs will be mutated. Otherwise,
            each ADF within the selected individuals is mutated with a
            probability of `per_adf_rate`.
        '''
        assert per_indiv_rate is not True, "per_indiv_rate has no value"
        assert per_adf_rate is not True, "per_adf_rate has no value"
        
        frand = rand.random
        
        do_all_indiv = (per_indiv_rate >= 1.0)
        do_all_adf = (per_adf_rate >= 1.0)
        
        def _edit(indiv):
            '''Returns a potentially edited individual.'''
            assert isinstance(indiv, TgpIndividual), "Want `TgpIndividual`, not `%s`" % type(indiv)
            
            bool_not = self._instr_bool_not
            bool_if = self._instr_bool_if
            
            new_genes = []
            for _, program in enumerate(indiv.genome):
                if do_all_adf or frand() < per_adf_rate:
                    new_program = [ ]
                    
                    # can't iterate since we need at least one lookahead
                    i = 0
                    while i < len(program):
                        instr = program[i]
                        next_instr = program[i+1] if i < len(program) - 1 else None
                        if instr == bool_not and next_instr == bool_not:
                            # Omit NOT NOT sequence from new program
                            i += 2
                        elif instr == bool_if and next_instr == bool_not:
                            # Replace IF NOT X Y Z with IF X Z Y
                            new_program.append(program[i])
                            expr_range = (i+2, self._find_end(program, i+2))
                            # false/true_range are named for where they will end up, not where they
                            # are being read from.
                            false_range = (expr_range[1], self._find_end(program, expr_range[1]))
                            true_range = (false_range[1], self._find_end(program, false_range[1]))
                            i = true_range[1]
                            new_program.extend(program[expr_range[0]:expr_range[1]])
                            new_program.extend(program[true_range[0]:true_range[1]])
                            new_program.extend(program[false_range[0]:false_range[1]])
                        else:
                            new_program.append(program[i])
                            i += 1
                    
                    new_genes.append(new_program)
                else:
                    new_genes.append(program)
            return new_genes
        
        for indiv in _source:
            if do_all_indiv or frand() < per_indiv_rate:
                yield type(indiv)(_edit(indiv), indiv, statistic={ 'mutated': 1, 'permutated': 1 })
            else:
                yield indiv
    
    @classmethod
    def _pick_random_node(cls, program, terminal_prob=None, allow_root=True):
        '''Selects a random branch within the program and returns both its
        starting index and end index (as found with `_find_end`).
        '''
        if not program:
            return (0, 0)
        
        start = rand.randrange(0 if allow_root else 1, len(program))
        if terminal_prob is None:
            pass
        elif rand.random() < terminal_prob:
            # find a terminal
            for start in xrange(start, start + len(program)):
                if program[start % len(program)].param_count == 0:
                    if allow_root or start % len(program):
                        break
            else:
                return (0, 0)
            start = start % len(program)    #pylint: disable=W0631
        else:
            # find a non-terminal
            for start in xrange(start, start + len(program)):
                if program[start % len(program)].param_count > 0:
                    if allow_root or start % len(program):
                        break
            else:
                return (0, 0)
            start = start % len(program)    #pylint: disable=W0631
        end = cls._find_end(program, start)
        
        return (start, end)
    
    @classmethod
    def _find_end(cls, program, start=0):
        '''Returns the index after the last parameter of the instruction starting
        at `start`.
        
        :Parameters:
          program : list(`Instruction`) [must support ``__getitem__``]
            The program to find the instruction parameters of.
          
          start : int [optional, defaults to 0]
            The index of the instruction to find the parameters of.
        
        :Returns:
            The index such that ``program[start:returned]`` contains an entire
            program branch.
        '''
        if start >= len(program):
            return start
        params = program[start].param_count
        end = start + 1
        while params > 0 and end < len(program):
            params += program[end].param_count - 1
            end += 1
        return end
