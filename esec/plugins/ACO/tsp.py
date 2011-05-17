#   Copyright 2010-2011 Steve Dower
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

'''TSP problem classes. 
'''

from itertools import chain, islice, izip
from math import sqrt
import esec.landscape as landscape
from esec.species.sequence import SequenceSpecies, SequenceIndividual
from esec.context import rand

#==============================================================================

class TourSpecies(SequenceSpecies):
    '''Provides individuals representing a tour.
    '''
    
    name = 'tour'
    
    def __init__(self, cfg, eval_default):
        super(TourSpecies, self).__init__(cfg, eval_default)
        # Make some names public within the execution context
        self.public_context['build_tours'] = self.init_tour
    
    def init_tour(self, cost_map, cost_power=2.0, pheromone_map=None, pheromone_power=2.0, greediness=0.0):
        '''Returns instances of `SequenceIndividual` based on cost and
        pheromone maps.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          cost_map : (int, int) -> float > 0 [optional]
            The cost associated with using a link from the first index
            value to the second. For example, ``cost_map[(2,4)]``
            contains the cost of using a link from node 2 to node 4.
            
            If an attractiveness matrix is used (higher values are
            preferred), specify a negative value for `cost_power`.
          
          cost_power : float [defaults to 2.0]
            The power to raise the cost value to when determining the
            probability of selecting a particular link.
            
            If `cost_map` is an attractiveness matrix (higher values are
            preferred), specify a negative value for this parameter.
          
          pheromone_map : `PheromoneMap` [optional]
            The pheromone map to use to generate the new tours.
            
            If omitted, pheromone information is not used when selecting
            links.
          
          pheromone_power : float [defaults to 2.0]
            The power to raise the pheromone value to when determining
            the probability of selecting a particular link.
          
          greediness : |prob| [defaults to 0.0]
            The probability of selecting the most attractive link rather
            than selecting an available link at random in proportion to
            attractiveness.
        '''
        irand = rand.randrange
        frand = rand.random
        
        length = max(cost_map)[0] + 1
        next_start_city = 0
        
        while True:
            # For each individual...
            
            # Starting location
            current_city = next_start_city
            next_start_city = (next_start_city + 1) % length
            
            # Remaining options
            options = set(xrange(length))
            options.discard(current_city)
            genes = [ current_city ]
            
            while options:
                prob_list = self._init_fitness_wheel(genes[-1], options,
                                                     cost_map, cost_power,
                                                     pheromone_map, pheromone_power)
                # Greedy selection
                next_city = prob_list[0][0]
                
                if greediness <= 0.0 or greediness < frand():
                    # Non-greedy selection
                    selection = frand() * sum(i[1] for i in prob_list)
                    
                    for city_index, prob in prob_list:
                        if selection < prob:
                            next_city = city_index
                            break
                        else:
                            selection -= prob
                
                genes.append(next_city)
                options.discard(next_city)
            
            # No options remaining, the link back to the original node
            # is handled elsewhere
            yield SequenceIndividual(genes, parent=self)
    
    @classmethod
    def _init_rank_wheel(cls, current_city, options, cost_map, cost_power, pheromone_map, pheromone_power):
        '''Produces a list of potential links and their attractiveness
        based on a ranking based on pheromone trail and cost.
        '''
        prob_list = cls._init_fitness_wheel(current_city, options, \
                                            cost_map, cost_power, \
                                            pheromone_map, pheromone_power)
        
        count = len(prob_list)
        return [(i[0], count - index) for index, i in enumerate(prob_list)]
    
    @classmethod
    def _init_fitness_wheel(cls, current_city, options, cost_map, cost_power, pheromone_map, pheromone_power):
        '''Produces a list of potential links and their attractiveness
        based on pheromone trail and cost.
        '''
        if cost_map:
            cost_list = ((i, cost_map[(current_city, i)]) for i in options)
        else:
            cost_power = 0
            cost_list = ((i, 1) for i in options)
        if pheromone_map:
            pher_list = ((i, pheromone_map[(current_city, i)]) for i in options)
        else:
            pheromone_power = 0
            pher_list = ((i, 1) for i in options)
        
        prob_list = sorted([(i, (c ** -cost_power if c else 1) * (p ** pheromone_power if p else 1)) \
                            for (i, c), (i2, p) in izip(cost_list, pher_list) if i == i2],
                           key=lambda i: i[1],
                           reverse=True)
        assert len(prob_list) == len(options)
        
        return prob_list

#==============================================================================
