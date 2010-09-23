'''A set of predefined pipelines that may be easily accessed using ``run.py``.

These pipelines may also be taken as examples to be used with configuration files.
'''

########################################################################
def _suitable_individual():
    '''Used by generic pipelines to create individuals suitable for the current
    landscape. In ESPDL it is accessible as ``suitable_individuals``.
    
    :Note:
        This is designed to be used by pipelines defined using `_make_config` and
        specified on the command line to ``run.py``. It deliberately takes no
        parameters to prevent abuse. To create more complex or specific
        individuals, write a new system definition.
    '''
    # Pipeline context is available through `context`
    lscape = context['cfg'].landscape
    assert hasattr(lscape, 'size'), "Landscapes used with predefined pipelines require a size attribute"
    
    if lscape.ltype == 'BVP':
        params = { 'shortest': lscape.size.min, 'longest': lscape.size.max }
        return context['random_binary'](**params)
    
    elif lscape.ltype == 'IVP':
        params = { 'shortest': lscape.size.min, 'longest': lscape.size.max,
                   'lowest': lscape.bounds[0], 'highest': lscape.bounds[1] }
        return context['random_int'](**params)
    
    elif lscape.ltype == 'RVP':
        params = { 'shortest': lscape.size.min, 'longest': lscape.size.max,
                   'lowest': lscape.bounds[0], 'highest': lscape.bounds[1] }
        return context['random_real'](**params)
    
    elif lscape.ltype == 'TGP':
        params = { 'terminals': lscape.terminals, 'deepest': lscape.size.get('init', 10) }
        if lscape.instruction_set == 'boolean':
            key = 'boolean_tgp'
        elif lscape.instruction_set == 'integer':
            key = 'integer_tgp'
        elif lscape.instruction_set == 'real':
            key = 'real_tgp'
            params['transcendentals'] = True
        else:
            key = 'boolean_tgp'
        return context[key](**params)
    
    elif lscape.ltype == 'GE':
        params = { 'grammar': lscape.rules, 'defines': getattr(lscape, 'defines', None),
                   'shortest': lscape.size.min, 'longest': lscape.size.max }
        return context['random_ge'](**params)
    
    else:
        raise ValueError(lscape.ltype + " is not recognised.")

def _make_config(definition, **extra):
    '''Puts `definition` into a dictionary suitable for overlaying by
    ``run.py``.
    '''
    cfg = {
        'system': {
            'definition': definition,
        }
    }
    cfg['system'].update(extra)
    return cfg

########################################################################

UN_DEF = r'''
FROM suitable_individuals SELECT (size) population
YIELD population

BEGIN generation
    YIELD population
END generation
'''
'''A simple unspecified (UN) evolutionary algorithm default

- As suggested by the unified model of De Jong as a baseline \cite{De2006}
- Generation based, non-overlapping
- No species operations specified.
'''

#-----------------------------------------------------------------------

GA_DEF = r'''
FROM suitable_individuals SELECT (size) population
YIELD population

BEGIN generation
    FROM population SELECT (size) offspring USING binary_tournament
    FROM offspring  SELECT population       USING crossover_one(per_pair_rate=0.8), \
                                                  mutate_random(per_indiv_rate=(1.0/size))
    YIELD population
END generation
'''
'''Genetic Algorithm.

- Binary (k=2) tournament selection of parent and mates
- One-point crossover and low random mutation (1/size rate)
- Generational model, non-overlapping parents and children
'''

#-----------------------------------------------------------------------

def _es_success_rate(parents, offspring):
    # each offspring is still matched with their parent
    count = 0
    for p,o in zip(parents, offspring):
        if o.fitness > p.fitness: count += 1
    return float(count) / float(len(parents))

def _es_adapt(current_step, adapt_step, success_rate):
    # Apply the 1/5th adaptive mutation rule and return the new step size
    if   success_rate > 0.21: return current_step * (1.0 + adapt_step)
    elif success_rate < 0.19: return current_step * (1.0 - adapt_step)
    else:                     return current_step

ES_DEF = r'''
FROM suitable_individuals SELECT (size) population
YIELD population

current_step = 1.0
adapt_step = 0.1

BEGIN generation
    FROM population SELECT 1 parent       USING uniform_random
    FROM parent     SELECT (size) parents USING repeat
    FROM parents    SELECT offspring      USING mutate_gaussian(step_size=current_step,per_gene_rate=1.0)
    YIELD offspring
    
    # calculate success rate based on parents and offspring
    success_rate = es_success_rate(parents, offspring)
    current_step = es_adapt(current_step, adapt_step, success_rate)
    
    FROM population, offspring SELECT (size) population USING best
    YIELD population
END generation
'''
'''Evolution Strategies. Uses adaptation of mutation parameters. Only
works for real valued problems.

- Clone and mutate only, no recombination
- Uniform random parent selection,
- Truncated best survivor selection
- Adaptive gaussian mutation
- Generational model (overlapping)
'''

#-----------------------------------------------------------------------

EP_DEF = r'''
FROM suitable_individuals SELECT (size) population
YIELD population

BEGIN generation
    FROM population SELECT offspring USING mutate_gaussian(step_size=1.0,per_gene_rate=1.0)
    
    FROM population, offspring SELECT (size) population USING best
    YIELD population
END generation
'''
'''Evolutionary Programming.

- Similar to ES with clone and mutate only variation (no recombination)
- Default to real value vector species and Gaussian mutation
- "Brood" breeding; each parent produces same number offspring (1:1)
- Generational model with overlapping competition (parents+offspring)

'''

#-----------------------------------------------------------------------

SSGA_DEF = r'''
FROM suitable_individuals SELECT (size) population
YIELD population

BEGIN generation
    REPEAT (size)
        FROM population SELECT 2 parents USING binary_tournament
        FROM parents    SELECT offspring USING crossover_one(per_pair_rate=0.9), \
                                               mutate_random(per_gene_rate=0.01)
        
        FROM offspring      SELECT 1 replacer       USING best
        FROM population     SELECT 1 replacee, rest USING uniform_shuffle
        FROM replacer, rest SELECT population
    END repeat

    YIELD population
END generation
'''

#-----------------------------------------------------------------------

NKC_GA_DEF = r'''
FROM random_binary(length=cfg.landscape.size.exact) SELECT (size) population
JOIN population, population INTO pairs USING random_tuples
EVAL pairs USING cfg.landscape
EVAL population USING assign(source=pairs)
YIELD population

BEGIN generation
    FROM population SELECT (size) offspring USING binary_tournament
    FROM offspring  SELECT population       USING crossover_one(per_pair_rate=0.8), \
                                                  mutate_random(per_indiv_rate=(1.0/size))
    
    JOIN population, population INTO pairs USING random_tuples
    EVAL pairs USING cfg.landscape
    EVAL population USING assign(pairs)
    `print '\n'.join(','.join(str(i) for i in p) for p in pairs)
    YIELD population
END generation
'''
'''Genetic Algorithm for NKC.

Includes a self-joining population and basic credit assignment.
'''

class _nkc_assign(object):
    def __init__(self, source):
        self.source = list(source)
    
    def eval(self, indiv):
        group = next((i for i in self.source if i[0] == indiv), None)
        if group: return group.fitness
        else: return None

#-----------------------------------------------------------------------

# `_make_config` is a shortcut to fill out the overlay dictionary.
configs = {
    'UN': _make_config(UN_DEF),
    'GA': _make_config(GA_DEF),
    'ES': _make_config(ES_DEF, es_success_rate=_es_success_rate, es_adapt=_es_adapt),
    'EP': _make_config(EP_DEF),
    'SSGA': _make_config(SSGA_DEF),
    'NKC_GA': _make_config(NKC_GA_DEF, assign=_nkc_assign),
}

# `default` contains some default values. They are here instead of in
# `configs` to allow plugins to override them.
default = {
    'system': {
        'suitable_individuals': _suitable_individual,
        'size': 10,
    }
}