'''Provides Evolutionary System Definition Language (ESDL) compilation
and validation.
'''

import re
from esec.utils.exceptions import ESDLSyntaxError

_ITER_DEF = '''
def _iter(*srcs):
    assert srcs, "srcs cannot be empty"
    def _conv(i):
        return (getattr(i, '__iter__', None) or getattr(i, '__call__'))()
    
    for src in srcs:
        for indiv in _conv(src):
            yield indiv'''
'''The definition of the ``_iter`` method used in compiled systems. This
automatically calls ``__iter__`` or ``__call__`` depending on the parameter
type, allowing constructors and lists to be intermixed. If multiple sequences
are provided they are concatenated.
'''

_BORN_ITER_DEF = '''
class _born_iter(object):
    def __init__(self, src):
        self.src = src
    
    def rest(self):
        seq = getattr(self.src, 'rest', self.src.__iter__)()
        return [i.born() for i in seq]
    
    def __iter__(self): return self
    
    def next(self):
        return next(self.src).born()'''
'''The definition of the ``_born_iter`` class used in compiled systems.
The primary purpose is to call the ``born`` method of individuals after
a ``FROM/SELECT`` statement. The secondary purpose is to handle calls to
``rest`` when the underlying sequence does not support it.
'''


class Compiler(object):
    '''Compiles ESDL into Python scripts.
    '''
    
    def __init__(self, src, context=None,
                 short_code=None, include_original=None):
        '''Initialises the compiler object but does not perform compilation or
        return any code.
        
        Call `compile` and then obtain transformed Python code from
        ``self.reset`` and ``self.breed``.
        
        :Parameters:
          src : str
            The ESDL code to compile. This string is stored in
            ``self.source_code`` and may be modified or replaced before
            calling `compile`.
          
          context : dict [optional]
            Extra definitions to include in the sandbox global variables.
            The contents are merged into ``self.context``. `context` is
            not modified and ``self.context`` must be used when executing
            the compiled code.
          
          short_code : bool [optional]
            When ``True``, attempts to produce less lines of code by
            nesting generator initialisers. This can make the code difficult
            to read but *may* provide some performance improvement.
            If not specified, short code is only produced when ``__debug__``
            is ``False``.
          
          include_original : bool [optional]
            When ``True``, adds comment lines containing the original source
            code.
            If not specified, these comments are only included when
            ``__debug__`` is ``True``.
        '''
        self.source_code = src
        self.context = dict(context) if context else {}
        self.short_code = (not __debug__) if short_code == None else short_code
        self.include_original = (__debug__) if include_original == None else include_original
        
        self._groups = None
        self.src_lines = None
        self.reset = None
        self.breed = None
    
    def compile(self):
        '''Compiles the source associated with this compiler object. The result
        is placed in ``self.reset`` and ``self.breed`` as strings.
        
        May raise `ESDLSyntaxError` if there are syntactical errors in
        ``self.source_code``. Further errors may be raised when executing the
        code produced.
        '''
        exec _ITER_DEF in self.context      #pylint: disable=W0122
        exec _BORN_ITER_DEF in self.context #pylint: disable=W0122
        
        self._groups = set()
        self.src_lines = list(self._filter_source(self.source_code))
        code_lines = list(self._transform(self.src_lines))
        code_blocks = [ [] ]
        for line in code_lines:
            if line == None:
                code_blocks.append([])
            else:
                code_blocks[-1].append(line)
        
        if len(code_blocks) > 2:
            raise ESDLSyntaxError('Code after generation definition.', ("ESDL", None, None, None))
        elif len(code_blocks) == 2:
            init_code = '\n'.join(('%s = _group()' % g for g in self._groups))
            self.reset = init_code + '\n' + '\n'.join(code_blocks[0])
            self.breed = '\n'.join(code_blocks[1])
        else:
            self.reset = None
            self.breed = None
            raise ESDLSyntaxError('No generation definition included.', ("ESDL", None, None, None))
    
    @classmethod
    def _hide_nested(cls, src):
        '''Returns a copy of `src` with the contents of all brackets or quotes
        replace by spaces.'''
        out = []
        nesting = []
        for char in src:
            out.append(' ' if nesting else char)
            
            if char in ('"', "'"):
                if not nesting or nesting[-1] != char:
                    nesting.append(char)
                    continue
            
            if not nesting or ('"' not in nesting and "'" not in nesting):
                if char == '(': nesting.append(')')
                elif char == '[': nesting.append(']')
                elif char == '{': nesting.append('}')
            
            if nesting and char == nesting[-1]:
                del nesting[-1]
                if not nesting:
                    out = out[:-1]
                    out.append(char)
        if nesting: raise EOFError
        return ''.join(out)
    
    def _filter_source(self, src):
        '''Returns a sequence of lines of code based on `src` with comments and
        empty lines omitted. White space at the start and end of lines is
        removed.'''
        hangover = ''
        lines = src.splitlines()
        for line_no, source_line in enumerate(lines):
            line = source_line.strip()
            if not line or line.startswith(('#', '//', ';')): continue
            line = hangover + line
            hangover = ''
            try:
                blanked = self._hide_nested(line)
                
                if '#' in blanked: blanked = blanked[:blanked.find('#')]
                if '//' in blanked: blanked = blanked[:blanked.find('//')]
                if ';' in blanked: blanked = blanked[:blanked.find(';')]
                line = line[:len(blanked)]
            except EOFError:
                if line[-1] != '\\':
                    line += '\\'
            
            if line[-1] == '\\':
                hangover = line[:-1].strip() + ' '
            else:
                yield (line_no, line)
                hangover = ''
        if hangover:
            raise ESDLSyntaxError("Unexpected end of definition", ("ESDL", len(lines), len(lines[-1]), lines[-1]))
    
    @classmethod
    def _cross_split(cls, src1, src2, sep):
        '''Splits `src1` at the positions where `sep` appears in `src2`.'''
        src = src1
        parts = src2.partition(sep)
        while parts[1]:
            yield src[:len(parts[0])]
            src = src[len(parts[0])+1:]
            parts = parts[2].partition(sep)
        yield src[:len(parts[0])]
    
    @classmethod
    def _cross_search(cls, src1, pattern, src2):
        '''Finds `pattern` in `src2` and returns the matching substring from `src1`.'''
        result = re.search(pattern, src2, re.IGNORECASE)
        if not result: return None
        start, end = result.span()
        return src1[start:end]
    
    # Prevent pylint complaining about complexity
    # (in order: returns/yields, branches, locals, lines)
    #pylint: disable=R0911,R0912,R0914,R0915
    def _transform(self, src):
        '''Transforms each line of code in `src` into one or more lines of
        Python code.
        
        :Parameters:
          src : iterable(``str``)
            The lines of code to compile.
        '''
        
        indent = ''
        opt_sc = self.short_code
        opt_io = self.include_original
        
        for (line_no, source_line) in src:
            blanked = self._hide_nested(source_line)
            parts = source_line.partition(' ')
            # All instructions are based on the first word.
            # If it is one of 'BEGIN', 'END', 'REPEAT', 'FROM', 'JOIN', 'EVAL' or 'YIELD',
            # we have a case to handle it. Otherwise, assume it is Python code and pass it
            # through unchanged.
            first_word = parts[0].upper()
            if first_word == 'BEGIN':
                second_word = parts[2].partition(' ')[0].upper()
                if second_word == 'GENERATION':
                    yield None
                    indent = ''
                else:
                    raise ESDLSyntaxError('Unrecognised parameter to BEGIN: ' + second_word,
                                          ("ESDL", line_no+1, None, source_line))
            
            
            elif first_word == 'END':
                indent = indent[:-4]
            
            
            elif first_word == 'REPEAT':
                if opt_io: yield indent + "# Line %02d: %s" % (line_no+1, source_line)
                
                yield indent + "for _ in xrange(%s):" % parts[2]
                indent += ' ' * 4
            
            
            elif first_word == 'FROM':
                if opt_io: yield indent + "# Line %02d: %s" % (line_no+1, source_line)
                
                src = self._cross_search(source_line, '(?<=FROM ).+(?= SELECT )', blanked)
                if src == None: raise ESDLSyntaxError("Expected SELECT", ("ESDL", line_no+1, None, source_line))
                
                dest = self._cross_search(source_line, '(?<= SELECT ).+(?= USING )', blanked)
                if dest == None: dest = self._cross_search(source_line, '(?<= SELECT ).+', blanked)
                if dest == None: raise ESDLSyntaxError("Invalid syntax", ("ESDL", line_no+1, None, source_line))
                dests = self._cross_split(dest, self._hide_nested(dest), ',')
                
                if opt_sc: _gen = "_iter(" + src.strip() + ")"
                else: yield indent + "_gen = _iter(" + src.strip() + ")"
                
                gens = self._cross_search(source_line, '(?<= USING ).+', blanked)
                if gens:
                    gens_blanked = self._hide_nested(gens)
                    
                    gen_list = [g.partition('(') for g in self._cross_split(gens, gens_blanked, ',')]
                    for gen in gen_list:
                        params = ')' if not gen[2] else ', ' + gen[2]
                        if opt_sc: _gen = "%s(%s%s" % (gen[0].strip(), _gen, params)
                        else: yield indent + "_gen = %s(_gen%s" % (gen[0].strip(), params)
                if opt_sc: _gen = "_born_iter(" + _gen + ")"
                else: yield indent + "_gen = _born_iter(_gen)"
                
                rest_done = False   # used to catch multiple unsized groups
                for dest in dests:
                    dest_count, _, dest = dest.strip().rpartition(' ')
                    self._groups.add(dest)
                    if dest_count: dest_count = dest_count.strip()
                    if dest_count:
                        if opt_sc and _gen:
                            yield indent + "_gen = " + _gen
                            _gen = None
                        try:
                            dest_count = int(dest_count)
                        except ValueError:
                            pass
                        if dest_count == 1: # only true if the above conversion succeeded
                            yield indent + "%s[:] = (next(_gen),)" % dest
                        else:
                            yield indent + "%s[:] = (next(_gen) for _ in xrange(%s))" % (dest, dest_count)
                    elif not rest_done:
                        if opt_sc and _gen: yield indent + "%s[:] = %s.rest()" % (dest, _gen)
                        else: yield indent + "%s[:] = _gen.rest()" % dest
                        rest_done = True
                    else:
                        raise ESDLSyntaxError("Multiple unsized destination groups", \
                                              ("ESDL", line_no+1, None, source_line))
            
            
            elif first_word == 'JOIN':
                if opt_io: yield indent + "# Line %02d: %s" % (line_no+1, source_line)
                
                src = self._cross_search(source_line, '(?<=JOIN ).+(?= INTO )', blanked)
                if src == None: raise ESDLSyntaxError("Expected INTO", ("ESDL", line_no+1, None, source_line))
                dest = self._cross_search(source_line, '(?<= INTO ).+(?= USING )', blanked)
                if dest == None: raise ESDLSyntaxError("Expected USING", ("ESDL", line_no+1, None, source_line))
                gen = self._cross_search(source_line, '(?<= USING ).+', blanked)
                if gen == None: gen = "_default_join"
                
                srcs = [s.strip() for s in src.split(',')]
                names = '["' + '", "'.join(srcs) + '"]'
                srcs = '[' + ', '.join(srcs) + ']'
                dest_count, _, dest = dest.strip().rpartition(' ')
                self._groups.add(dest)
                gen, _, params = gen.partition('(')
                
                params = ')' if not params else ', ' + params
                if opt_sc:
                    yield indent + "%s[:] = %s(%s, %s%s" % (dest, gen, srcs, names, params)
                else:
                    yield indent + "_gen = %s(%s, %s%s" % (gen, srcs, names, params)
                    yield indent + "%s[:] = _gen" % dest
            
            
            elif first_word in ('EVAL', 'EVALUATE'):
                if opt_io: yield indent + "# Line %02d: %s" % (line_no+1, source_line)
                
                dest = self._cross_search(source_line, '(?<=' + first_word + ' ).+(?= USING )', blanked)
                if dest:
                    gen = self._cross_search(source_line, '(?<= USING ).+', blanked)
                    if gen == None: raise ESDLSyntaxError("Expected evaluator", ("ESDL", line_no+1, None, source_line))
                    
                    yield indent + "_eval = %s if hasattr(%s, 'eval') else %s()" % (gen, gen, gen)
                    yield indent + "for _indiv in %s:" % dest
                    yield indent + "    _indiv._eval = _eval"
                    yield indent + "    del _indiv.fitness"
                else:
                    dest = self._cross_search(source_line, '(?<=EVAL ).+', blanked)
                    yield indent + "for _indiv in %s:" % dest
                    yield indent + "    _indiv._eval = None"
                    yield indent + "    del _indiv.fitness"
            
            
            elif first_word == 'YIELD':
                if opt_io: yield indent + "# Line %02d: %s" % (line_no+1, source_line)
                
                srcs = self._cross_search(source_line, '(?<=YIELD ).+', blanked)
                if srcs == None:
                    raise ESDLSyntaxError("Expected group or groups", ("ESDL", line_no+1, None, source_line))
                
                for src in (s.strip() for s in srcs.split(',')):
                    yield indent + "_on_yield('%s', %s)" % (src, src)
            
            
            else:
                if source_line[0] == '`': source_line = source_line[1:]
                if opt_io: yield indent + "# Line %02d: %s" % (line_no+1, source_line)
                assign = re.match('[ ]*([a-zA-Z_][a-zA-Z0-9_]*)[ ]*=', source_line)
                if assign:
                    self.context[assign.groups()[0]] = None
                yield indent + source_line

