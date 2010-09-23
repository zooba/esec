#   Copyright 2010 Clinton Woodward and Steve Dower
# 
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from esec.utils import ConfigDict, is_ironpython

config = {
    'random_seed': 1,
    'landscape': {
        'random_seed': 1
    },
    'monitor': {
        'limits': { 'generations': 10 },
        'report': 'brief_header+gen+evals+local_header+local_min+local_ave+local_max+' + \
                  'time+time_delta+time_precise+time_delta_precise+' + \
                  'local_best_phenome',
        'summary': 'gen+best_fit+evals+status+time+time_precise+' + \
                   'best_genome+best_length+best_phenome'
    },
    'system': {
        'size': 10
    },
    'verbose': 0,
}

settings = "low_priority=True;"

std_dialects = ['GA', 'SSGA']
bvp_tests = [
    ('BVP.OneMax',      std_dialects, [{ 'landscape': { 'N': 3 } }, { 'landscape': { 'N': 8 } }, { 'landscape': { 'N': 100 } }]),
    ('BVP.RoyalRoad',   std_dialects, [{ 'landscape': { 'C': 3, 'Q': 4 } }, { 'landscape': { 'C': 8, 'Q': 6 } }]),
    ('BVP.GoldbergD3B', std_dialects, [{ 'landscape': { 'N': 3 } }, { 'landscape': { 'N': 10 } }, { 'landscape': { 'N': 100 } }]),
    ('BVP.WhitleyD4B',  std_dialects, [{ 'landscape': { 'N': 3 } }, { 'landscape': { 'N': 10 } }, { 'landscape': { 'N': 100 } }]),
    ('BVP.Multimodal',  std_dialects, [{ 'landscape': { 'N': 10, 'P': 4 } }, { 'landscape': { 'N': 100, 'P': 20 } }]),
    ('BVP.CNF_SAT',     std_dialects, [{ 'landscape': { 'SAW': False } }, { 'landscape': { 'SAW': True } }]),
    ('BVP.NK',          std_dialects, [{ 'landscape': { 'N': 5, 'K': 2 } }, { 'landscape': { 'N': 10, 'K': 4 } }]),
    ('BVP.NKC',         ['NKC_GA'],     [{ 'landscape': { 'N': 5, 'K': 2, 'C': 2 } }, { 'landscape': { 'N': 10, 'K': 4, 'C': 2 } }]),
    ('BVP.MMDP6',       std_dialects, [{ 'landscape': { 'subs': 5 } }, { 'landscape': { 'subs': 20 } }]),
    ('BVP.ECC',         std_dialects, [{ 'landscape': { 'n': 2, 'M': 2, 'd': 1 } }, { 'landscape': { 'n': 6, 'M': 6, 'd': 3 } }]),
    ('BVP.SUS',         std_dialects, [{ 'landscape': { 'even': False } }, { 'landscape': { 'even': True } }]),
    ('BVP.MAXCUT',      std_dialects, [{ 'landscape': { 'N': 2, 'P': 0.9 } }, { 'landscape': { 'N': 4, 'P': 0.5 } }]),
    ('BVP.MTTP',        std_dialects, [{ 'landscape': { 'tasks': 20 } }, { 'landscape': { 'tasks': 40 } }]),
    ('BVP.Graph2c',     std_dialects, [{ 'landscape': { 'parameters': 20 } }, { 'landscape': { 'parameters': 50 } }]),
    ('BVP.Graph2r',     std_dialects, [{ 'landscape': { 'parameters': 20 } }, { 'landscape': { 'parameters': 50 } }]),
]

std_dialects = ['GA', 'SSGA', 'binary_int_map']
ivp_tests = [
    ('IVP.Nsum',        std_dialects, [{ 'landscape': { 'size': { 'exact': 20 } } }, { 'landscape': { 'size': { 'min': 10, 'max': 50 } } }]),
    ('IVP.Nmax',        std_dialects, [{ 'landscape': { 'size': { 'exact': 20 } } }, { 'landscape': { 'size': { 'min': 10, 'max': 50 } } }]),
    ('IVP.Nmatch',      std_dialects, [{ 'landscape': { 'size': { 'exact': 20 } } }, { 'landscape': { 'size': { 'min': 10, 'max': 50 } } }]),
    ('IVP.Robbins',     std_dialects, [{ 'landscape': { 'size': { 'exact': 20 } } }, { 'landscape': { 'size': { 'min': 10, 'max': 50 } } }]),
]

std_dialects = ['GA', 'SSGA', 'binary_real_map']
rvp_tests = [
    ('RVP.Linear',          std_dialects, [{ 'landscape': { 'size': { 'exact': 20 } } }, { 'landscape': { 'size': { 'min': 10, 'max': 50 } } }]),
    ('RVP.Neutral',         std_dialects, [None, { 'landscape': { 'size': { 'min': 1, 'max': 10 } } }]),
    ('RVP.Stabilising',     std_dialects, [None, { 'landscape': { 'size': { 'min': 1, 'max': 10 } } }]),
    ('RVP.Disruptive',      std_dialects, [None, { 'landscape': { 'size': { 'min': 1, 'max': 10 } } }]),
    ('RVP.Sphere',          std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.Ellipsoid',       std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.HyperEllipsoid',  std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.Quadric',         std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.NoisyQuartic',    std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.Easom',           std_dialects, [None]),
    ('RVP.Rosenbrock',      std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.Rastrigin',       std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.Griewangk',       std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.Ackley',          std_dialects, [None, { 'landscape': { 'size': { 'exact': 10 } } }]),
    ('RVP.Schwefel',        std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.Michalewicz',     std_dialects, [None, { 'landscape': { 'size': { 'min': 2, 'max': 10 } } }]),
    ('RVP.MultiPeak1',      std_dialects, [None]),
    ('RVP.MultiPeak2',      std_dialects, [None]),
    ('RVP.MultiPeak3',      std_dialects, [None]),
    ('RVP.MultiPeak4',      std_dialects, [None]),
    ('RVP.Booth',           std_dialects, [None]),
    ('RVP.Himmelblau',      std_dialects, [None]),
    ('RVP.SixHumpCamelBack', std_dialects, [None]),
    ('RVP.FMS',             std_dialects, [None]),
]

tgp_tests = [
    ('TGP.Multiplexer',         ['TGP_BOOL_%d'], [None]),
    ('TGP.SymbolicRegression',  ['TGP_INT_%d', 'TGP_REAL_%d'], [None]),
]

std_dialects = ['GA', 'SSGA']
ge_tests = [
    ('GE.Multiplexer',          std_dialects, [None]),
    ('GE.SymbolicRegression',   std_dialects, [None]),
]

TGP_DEF_TEMPLATE = r'''
FROM %s_tgp(terminals=cfg.landscape.terminals,%s) SELECT (size) population
YIELD population

BEGIN generation
    FROM population SELECT (size) offspring USING binary_tournament
    FROM offspring  SELECT population       USING crossover_one(per_pair_rate=0.8), \
                                                  mutate_random(per_indiv_rate=(1.0/size))
    YIELD population
END generation
'''

TGP_BOOL_DEFS = [TGP_DEF_TEMPLATE % i for i in [('boolean', 'constants=False'), ('boolean', 'constants=True')]]
TGP_INT_DEFS =  [TGP_DEF_TEMPLATE % i for i in [('integer', ''), ('integer', 'lowest_constant=0, highest_constant=255')]]
TGP_REAL_DEFS = [TGP_DEF_TEMPLATE % i for i in [('real', ''), ('real', 'transcendentals=True'), ('real', 'lowest_constant=-1.0, highest_constant=1.0')]]

REAL_MAP_DEF = r'''FROM random_real_binary(longest=cfg.landscape.size.max*10,shortest=cfg.landscape.size.min*10, \
                        resolution=cfg.landscape.bounds[1][0]-cfg.landscape.bounds[0][0] / 10.0, \
                        offset=cfg.landscape.bounds[0][0], \
                        bits_per_value=10) SELECT (size) population

YIELD population

BEGIN generation
    FROM population SELECT (size) offspring USING binary_tournament
    FROM offspring  SELECT population       USING crossover_one(per_pair_rate=0.8), \
                                                  mutate_bitflip(per_gene_rate=0.1)
    YIELD population
END generation
'''

INT_MAP_DEF = r'''FROM random_integer_binary(longest=cfg.landscape.size.max*10,shortest=cfg.landscape.size.min*10, \
                        resolution=cfg.landscape.bounds[1][0]-cfg.landscape.bounds[0][0] / 10, \
                        offset=cfg.landscape.bounds[0][0], \
                        bits_per_value=10) SELECT (size) population

YIELD population

BEGIN generation
    FROM population SELECT (size) offspring USING binary_tournament
    FROM offspring  SELECT population       USING crossover_one(per_pair_rate=0.8), \
                                                  mutate_bitflip(per_gene_rate=0.1)
    YIELD population
END generation
'''
configs = {
    'binary_real_map': {
        'system': {
            'definition': REAL_MAP_DEF
        }
    },
    'binary_int_map': {
        'system': {
            'definition': INT_MAP_DEF
        }
    }
}

for i, d in enumerate(TGP_BOOL_DEFS): configs['TGP_BOOL_%d' % i] = { 'system': { 'definition': d } }
for i, d in enumerate(TGP_INT_DEFS):  configs['TGP_INT_%d'  % i] = { 'system': { 'definition': d } }
for i, d in enumerate(TGP_REAL_DEFS): configs['TGP_REAL_%d' % i] = { 'system': { 'definition': d } }

tests = bvp_tests + ivp_tests + rvp_tests + tgp_tests + ge_tests
#tests = bvp_tests
#tests = ivp_tests
#tests = rvp_tests
#tests = tgp_tests
#tests = ge_tests

# return (tags, cmd string, config, settings, report)
def batch():
    for (k,dialects,testconfigs) in tests:
        for d in dialects:
            if d[-2:] == '%d':
                i = 0
                d2 = d % i
                while d2 in configs:
                    for c in testconfigs:
                        cfg = ConfigDict(config)
                        if c: cfg.overlay(c)
                        yield ([k.partition('.')[0]], '%s+%s' % (k, d2), cfg, None, None)
                    i += 1
                    d2 = d % i
            else:
                for c in testconfigs:
                    cfg = ConfigDict(config)
                    if c: cfg.overlay(c)
                    yield ([k.partition('.')[0]], '%s+%s' % (k, d), cfg, None, None)
        