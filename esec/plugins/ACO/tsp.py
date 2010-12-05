#   Copyright 2010 Steve Dower
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

import esec.landscape as landscape
from esec.species.integer import IntegerSpecies, IntegerIndividual
from esec.context import rand
from math import sqrt

#==============================================================================

class TourIndividual(IntegerIndividual):
    '''An `Individual` with tour genomes. These individuals are used with
    `TourSpecies` and `tsp.Landscape` to solve the Travelling Salesman Problem.
    
    The genome is a list of nodes in the order that they are visited, represented
    as integer values. The phenome is a list of pairs (tuples) of nodes, each
    representing a link from the first node to the second node.
    '''
    
    @property
    def phenome(self):
        '''Returns the phenome of this individual. The phenome is a list
        of pairs (tuples) of nodes, each representing a link from the first
        node to the second node.
        '''
        p = [ ]
        current = self.genome[0]
        for g in self.genome[1:]:
            p.append((current, g))
            current = g
        p.append((current, self.genome[0]))
        return p
    
    @property
    def phenome_string(self):
        '''Returns a string representation of the phenome of this individual.
        '''
        return ' -> '.join(str(i) for i in self.genome)

#==============================================================================

class TourSpecies(IntegerSpecies):
    '''Provides individuals representing a tour.
    '''
    
    name = 'tour'
    
    def __init__(self, cfg, eval_default):
        super(TourSpecies, self).__init__(cfg, eval_default)
        # Make some names public within the execution context
        self.public_context['build_tours'] = self.init_tour
    
    def init_tour(self, cost_map, cost_power=2.0, pheromone_map=None, pheromone_power=2.0, greediness=0.0):
        '''Returns instances of `TourIndividual`.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          cost_map : mapping from tuples of integers to integers > 0 [optional]
            The cost associated with using a link from the first index value to the
            second. For example, ``cost_map[(2,4)]`` contains the cost of using a link
            from node 2 to node 4.
            
            If an attractiveness matrix is used (higher values are preferred), specify
            a negative value for `cost_power`.
          
          cost_power : float [defaults to 2.0]
            The power to raise the cost value to when determining the probability of
            selecting a particular link.
            
            If `cost_map` is an attractiveness matrix (higher values are preferred),
            specify a negative value for this parameter.
          
          pheromone_map : `PheromoneMap` [optional]
            The pheromone map to use to generate the new tours.
            
            If omitted, pheromone information is not used when selecting links.
          
          pheromone_power : float [defaults to 2.0]
            The power to raise the pheromone value to when determining the probability
            of selecting a particular link.
          
          greediness : |prob| [defaults to 0.0]
            The probability of selecting the most attractive link rather than selecting
            an available link at random in proportion to attractiveness.
        '''
        irand = rand.randrange
        frand = rand.random
        
        length = max(cost_map)[0] + 1
        lower_bounds = [0] * length
        upper_bounds = [length - 1] * length
        
        while True:
            # For each individual...
            
            # Fixed starting location
            current_city = 0
            # Random stating location
            #current_city = irand(length)
            
            # Remaining options
            options = set(xrange(length))
            options.discard(current_city)
            genes = [ current_city ]
            
            while options:
                prob_list = self._init_fitness_wheel(current_city, options, \
                                                     cost_map, cost_power, \
                                                     pheromone_map, pheromone_power)
                total = sum(i[1] for i in prob_list)
                if greediness <= 0.0 or greediness < frand():
                    # Non-greedy selection
                    selection = frand() * total

                    next_city = prob_list[0][0]
                    i = 0
                    while selection > 0.0:
                        selection -= prob_list[i][1]
                        i += 1
                    i -= 1
                    if 0 < i < len(prob_list): next_city = prob_list[i][0]
                else:
                    # Greedy selection
                    next_city = prob_list[0][0]
                
                current_city = next_city
                genes.append(current_city)
                options.discard(current_city)
            
            # No options remaining, the link back to the original node is handled elsewhere
            yield TourIndividual(genes, parent=self, lower_bounds=lower_bounds, upper_bounds=upper_bounds)
    
    @classmethod
    def _init_rank_wheel(cls, current_city, options, cost_map, cost_power, pheromone_map, pheromone_power):
        '''Produces a list of potential links and their attractiveness based on
        a ranking based on pheromone trail and cost.
        '''
        prob_list = cls._init_fitness_wheel(current_city, options, \
                                            cost_map, cost_power, \
                                            pheromone_map, pheromone_power)
        
        count = len(prob_list)
        return [(i[0], count - index) for index, i in enumerate(prob_list)]
    
    @classmethod
    def _init_fitness_wheel(cls, current_city, options, cost_map, cost_power, pheromone_map, pheromone_power):
        '''Produces a list of potential links and their attractiveness based on
        pheromone trail and cost.
        '''
        if cost_map:
            cost_list = [(i, cost_map[(current_city, i)]) for i in options]
        else:
            cost_power = 0
            cost_list = [(i, 1) for i in options]
        if pheromone_map:
            pher_list = [(i, pheromone_map[(current_city, i)]) for i in options]
        else:
            pheromone_power = 0
            pher_list = [(i, 1) for i in options]
        
        prob_list = [(i, (c ** -cost_power if c else 1) * (p ** pheromone_power if p else 1)) \
                     for (i, c), (i2, p) in zip(cost_list, pher_list) if i == i2]
        assert len(prob_list) == len(options)
                
        return sorted(prob_list, key=lambda i: i[1], reverse=True)

#==============================================================================

class Landscape(landscape.Landscape):
    '''TSP fitness landscape.
    '''
    ltype = 'ACO'
    lname = 'TSP'
    maximise = False
    
    syntax = {
        # cost_map can contain one of five formats:
        #   - full cost matrix (eg. [ [ None, 1, 2, 3 ], [ 1, None, 4, 5 ], [ 2, 4, None, 6 ], [ 3, 5, 6, None ] ])
        #   - half cost matrix, symmetrical about the start of each item (eg. [ [ 1, 2, 3], [ 4, 5 ], [ 6 ] ])
        #   - node list, each element contains a node index, X-coordinate and Y-coordinate
        #     (the node index is optional, but must be the first value specified if it is included)
        #     (eg. [ [12.5, 4.3], [4.3, 8.3] ... ] or [ [1, 12.5, 4.3], [2, 4.3, 8.3], ... ])
        #   - the path to a CSV file containing one of the above three formats
        #   - a dictionary mapping tuples of integers to the cost of including a link from the first to
        #     the second (eg. { (0, 0): None, (0, 1): 1, (0, 2): 2, (0, 3): 3, (1, 0): 1, ... })
        'cost_map': '*',
        # invalid_fitness is the fitness value to return when an individual is
        # not valid.
        'invalid_fitness': [int, float]
    }
    
    default = {
        'cost_map': [
            [ None, 1, 2, 3, 7 ],
            [ 1, None, 2, 1, 5 ],
            [ 2, 2, None, 3, 9 ],
            [ 3, 1, 3, None, 4 ],
            [ 7, 5, 9, 4, None ],
        ],
        'invalid_fitness': 1.0e9
    }
    
    berlin52_map = [
         (565.0, 575.0),   (25.0, 185.0),   (345.0, 750.0),  (945.0, 685.0),  (845.0, 655.0),  (880.0, 660.0), \
          (25.0, 230.0), (525.0, 1000.0),  (580.0, 1175.0), (650.0, 1130.0), (1605.0, 620.0), (1220.0, 580.0), \
        (1465.0, 200.0),   (1530.0, 5.0),   (845.0, 680.0),  (725.0, 370.0),  (145.0, 665.0),  (415.0, 635.0), \
         (510.0, 875.0),  (560.0, 365.0),   (300.0, 465.0),  (520.0, 585.0),  (480.0, 415.0),  (835.0, 625.0), \
         (975.0, 580.0), (1215.0, 245.0),  (1320.0, 315.0), (1250.0, 400.0),  (660.0, 180.0),  (410.0, 250.0), \
         (420.0, 555.0),  (575.0, 665.0), (1150.0, 1160.0),  (700.0, 580.0),  (685.0, 595.0),  (685.0, 610.0), \
         (770.0, 610.0),  (795.0, 645.0),   (720.0, 635.0),  (760.0, 650.0),  (475.0, 960.0),   (95.0, 260.0), \
         (875.0, 920.0),  (700.0, 500.0),   (555.0, 815.0),  (830.0, 485.0),  (1170.0, 65.0),  (830.0, 610.0), \
         (605.0, 625.0),  (595.0, 360.0),  (1340.0, 725.0), (1740.0, 245.0)
    ]
    '''A coordinate map for the Berlin 52 cities landscape.
    
    When specified as a cost map, the constructor will automatically determine the distance
    between each node.
    '''
    
    strict = { }
    
    test_key = ( )
    test_cfg = ( )
    
    def __init__(self, cfg=None, **other_cfg):
        # call parent cfg magic, validate/strict test syntax/defaults/cfg
        super(Landscape, self).__init__(cfg, **other_cfg)
        
        self.invalid_fitness = self.cfg.invalid_fitness
        self.cost_map = self.cfg.cost_map
        
        if isinstance(self.cost_map, str):
            with open(self.cost_map) as source:
                self.cost_map = [[float(i) for i in line.split(',')] for line in source]
        
        # Not elif to allow node conversion if necessary
        if isinstance(self.cost_map, (list, tuple)) and isinstance(self.cost_map[0], (list, tuple)):
            # Convert list-of-lists to dictionary lookup
            cost_map = { }
            if len(self.cost_map) == len(self.cost_map[0]):
                # Dimensions are equal, so assume cost matrix
                
                if len(self.cost_map[1]) == len(self.cost_map[0]):
                    # Dimensions remain equal, so assume full matrix
                    for i in xrange(len(self.cost_map)):
                        for j in xrange(len(self.cost_map[i])):
                            cost_map[(i, j)] = self.cost_map[i][j]
                        cost_map[(i, i)] = None
                
                elif len(self.cost_map[1]) == len(self.cost_map[0]) - 1:
                    # Dimensions reduce, so assume half matrix
                    for i in xrange(len(self.cost_map)):
                        cost_map[(i, i)] = None
                        for j in xrange(len(self.cost_map[i])):
                            cost_map[(i, j + i + 1)] = self.cost_map[i][j]
                            cost_map[(j + i + 1, i)] = self.cost_map[i][j]
                
                cost_map[(len(self.cost_map), len(self.cost_map))] = None
                
            elif len(self.cost_map[0]) == 2:
                # Nested dimension is 2, so assume list of coordinates
                for i, (x1, y1) in enumerate(self.cost_map):
                    for j, (x2, y2) in enumerate(self.cost_map):
                        if i == j:
                            cost_map[(i, j)] = None
                        else:
                            x = x2 - x1
                            y = y2 - y1
                            cost_map[(i, j)] = sqrt(x*x + y*y)
            elif len(self.cost_map[0]) == 3:
                # Nested dimension is 3, so assume list of coordinates with leading index
                for i, (_, x1, y1) in enumerate(self.cost_map):
                    for j, (_, x2, y2) in enumerate(self.cost_map):
                        if i == j:
                            cost_map[(i, j)] = None
                        else:
                            x = x2 - x1
                            y = y2 - y1
                            cost_map[(i, j)] = sqrt(x*x + y*y)
            self.cost_map = cost_map
    
    def _eval(self, indiv):
        '''Determines the length of a given tour.'''
        cost_map = self.cost_map
        cost = 0.0
        
        assert isinstance(indiv, TourIndividual), "Expected 'TourIndividual', not '%s'" % type(indiv).__name__
        assert all(p in cost_map for p in indiv.phenome), \
            "Cost map is incomplete: missing %s" % next(p not in cost_map for p in indiv.phenome)
        
        for p in indiv.phenome:
            try:
                cost += cost_map[p]
            except KeyError:
                return self.invalid_fitness
        
        return cost
        
    def info(self, level):
        '''Return the basics and, if `level` > 3, the cost map.
        '''
        result = super(Landscape, self).info(level)
        if not self.cost_map:
            result.append("Cost map: None")
        elif (level > 3 and len(self.cost_map) < 1000) or level > 4:
            result.append("Cost map:")
            line = ''
            last = None
            map_items = sorted(self.cost_map.iteritems(), key=lambda i: i[0])
            for cost in map_items:
                if last == None: last = cost[0][0]
                if last != cost[0][0]:
                    result.append(line)
                    line = ''
                    last = cost[0][0]
                
                if isinstance(cost[1], (int, float)):
                    line += '%8.2f ' % cost[1]
                else:
                    line += '%8s ' % (cost[1],)
            result.append(line)
        else:
            d = max(self.cost_map.iterkeys())
            d = (d[0] + 1, d[1] + 1)
            result.append('Cost map: {%dx%d}' % d)
            if level > 3:
                result[-1] += ' (Set verbosity to 5 to display.)'
        return result

#==============================================================================
