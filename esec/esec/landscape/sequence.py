'''Sequence problem landscapes.

The `Sequence` base class inherits from `Landscape` for parameter
validation and support. See `landscape` for details.
'''

from sys import maxsize
from math import sqrt
from itertools import chain, islice, izip
from esec.species.sequence import SequenceIndividual
from esec.landscape import Landscape
import esec.utils

#=======================================================================
class Sequence(Landscape):
    '''Abstract integer-valued parameter fitness landscape
    '''
    ltype = 'SEQ' # subclasses shouldn't change this
    ltype_name = 'Sequence'
    
    # This is universal for Sequence problems
    syntax = { }
    
    # Subclasses can set default to overlay their changes on to this
    default = { }
    
    test_key = ( )
    test_cfg = ( ) #n=params #low-bounds #high-bounds
    
    def __init__(self, cfg=None, **other_cfg):
        # call parent cfg magic, validate/strict test syntax/defaults/cfg
        super(Sequence, self).__init__(cfg, **other_cfg)
    
    def legal(self, indiv):
        '''Check to see if an individual is legal.'''
        return True

#=======================================================================
class SimplePacking(Sequence):
    '''A simple packing problem. The fitness is the amount of free space
    remaining multipled by the number of boxes used.
    '''
    lname = 'Packing'
    maximise = False
    
    syntax = {
        'item_sizes': '*',
        'box_size': [int, float]
    }
    
    default = {
        'item_sizes': [ 1.0, 1.0, 2.0, 2.0, 4.0, 5.0, 7.0, 7.0, 8.0 ],
        'box_size': 9,
    }
    
    def __init__(self, cfg=None, **other_cfg):
        super(SimplePacking, self).__init__(cfg, **other_cfg)
        self.size.min = self.size.max = self.size.exact = len(self.cfg.item_sizes)
    
    def phenome_string(self, indiv):
        '''Produces a string representation of `indiv`.'''
        result = ''
        items = self.cfg.item_sizes
        box_size = self.cfg.box_size
        space_in_current_box = None
        for size in (items[i] for i in indiv):
            if space_in_current_box is None:
                result += '[ '
                space_in_current_box = box_size
            elif size > space_in_current_box:
                result += '(%.1f) ] [ ' % space_in_current_box
                space_in_current_box = box_size
            
            space_in_current_box -= size
            result += '%.1f ' % size

        return result + '(%.1f) ]' % space_in_current_box
    
    def _eval(self, indiv):
        '''Sum of the free space, multipled by the number of boxes.'''
        if indiv.legal():
            wasted_space = 0.0
            items = self.cfg.item_sizes
            box_size = self.cfg.box_size
            
            space_in_current_box = box_size
            box_count = 1
            packed = []
            
            for i in indiv:
                size = items[i]
                assert size <= box_size, "Items cannot be bigger than an entire box"
                
                if size > space_in_current_box:
                    wasted_space += space_in_current_box
                    space_in_current_box = box_size - size
                    box_count += 1
                else:
                    space_in_current_box -= size
            
            return (space_in_current_box + wasted_space) * box_count
        else:
            return float('inf')

#=======================================================================

class TSP(Sequence):
    '''TSP fitness landscape.
    '''
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
    }
    
    default = {
        'cost_map': [
            [ None, 1, 2, 3, 7 ],
            [ 1, None, 2, 1, 5 ],
            [ 2, 2, None, 3, 9 ],
            [ 3, 1, 3, None, 4 ],
            [ 7, 5, 9, 4, None ],
        ],
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
    
    When specified as a cost map, the constructor will automatically
    determine the distance between each node.
    '''
    
    strict = { }
    
    test_key = ( )
    test_cfg = ( )
    
    def __init__(self, cfg=None, **other_cfg):
        # call parent cfg magic, validate/strict test syntax/defaults/cfg
        super(TSP, self).__init__(cfg, **other_cfg)
        
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
        
        d = max(self.cost_map.iterkeys())
        d = (d[0] + 1, d[1] + 1)
        self.size.min = self.size.max = self.size.exact = min(d)
    
    def phenome_string(self, indiv):
        '''Produces a string representation of `indiv`.'''
        return ' -> '.join(str(i + 1) for i in indiv)
    
    def _eval(self, indiv):
        '''Determines the length of a given tour.'''
        cost_map = self.cost_map
        cost = 0.0
        
        assert isinstance(indiv, SequenceIndividual), \
            "Expected 'SequenceIndividual', not '%s'" % type(indiv).__name__
        
        if not indiv.legal():
            return float('inf')
        
        assert all(p in cost_map for p in esec.utils.overlapped_pairs(indiv.phenome)), \
            "Cost map is incomplete: missing %s" % \
            next(p not in cost_map for p in esec.utils.overlapped_pairs(indiv.phenome))
        
        try:
            return sum(cost_map[p] for p in esec.utils.overlapped_pairs(indiv.phenome))
        except KeyError:
            return float('inf')
    
    def info(self, level):
        '''Return the basics and, if `level` > 3, the cost map.
        '''
        result = super(TSP, self).info(level)
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

#=======================================================================
