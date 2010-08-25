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

from esec.utils.configdict import ConfigDict
from esec.landscape import ge as landscape

config = {
    'landscape': {
        'class': landscape.Multiplexer,
        'size': { 'max': 100 },
        'wrap_count': 10,
        'size_penalty_square_factor': 0.0,
        'size_penalty_linear_factor': 0.1,
    },
    'monitor': {
        'report': 'gen+births+best_header+best+stable_count+best_length+|+' + \
                  'local+local_no_compile+local_unique+|+time_delta',
        'summary': 'status+best_bday+best_fit+best_length+best_phenome',
        'limits': {
            'generations': 10000,
            'fitness': 2048,
            'stable': 100,
        },
    },
}

settings = ''
settings += 'pathbase="results/GEMultiplexer3";'
settings += 'csv=True;low_priority=True;'

def batch():
    while True:
        yield ([], "noseed+SSGA", config, None, None)
