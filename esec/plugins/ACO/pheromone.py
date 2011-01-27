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

'''General pheromone map class.
'''

#==============================================================================

class PheromoneMap(object):
    '''Represents a pheromone map. This class provides a mapping from phenome
    values to pheromone values. The `update_fitness` and `update_rank` functions
    (or the `update` function) may be used to reinforce the pheromone for the
    phenome components used in the provided individuals while reducing the
    remainder.
    
    Custom pheromone maps may be implemented for different problems. To allow
    interoperability between different implementations, it is recommended that
    the `__getitem__` method be retained to retrieve the pheremone value for
    a given phenome component.
    '''
    def __init__(self, initial=0.1):
        '''Initialises a new pheromone map.
        
        :Parameter:
          initial : float
            The initial pheromone. It is generally recommended that this be
            greater than zero.
        '''
        self.initial = initial
        self._pheromone = { }
        
    def __getitem__(self, key):
        return self._pheromone.get(key, self.initial)
    
    def update_fitness(self, source, strength=0.1, minimisation=False, minimization=None, persistence=0.9):
        '''Updates the pheromone map. This method is intended to be called directly
        from a system definition each generation.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          source : iterable(`Individual`)
            A sequence of individuals. The fitness values of these individuals
            are used to increase pheromone levels.
          
          strength : float [defaults to 0.1]
            The multiplier to apply to fitness values when adding to the pheromone value.
            
            Only the first part of the fitness value is used. Multi-part fitnesses should
            ensure that their first value is suitable for this use, or create a new
            pheromone map that can handle multiple parts correctly.
          
          minimisation : boolean [defaults to ``False``]
            If ``True``, the reciprocal of fitness values are used. If a lower fitness
            represents a better solution, this should be ``True`` to ensure a larger effect
            on the pheromone.
          
          minimization : boolean [defaults to ``False``]
            A synonym for `minimisation`. If specified, this value is used in preference to
            `minimisation`.
          
          persistence : |prob|
            The fraction of pheromone to retain on each update. Every pheromone value is
            multiplied by this value on each update. 'Decay' values subtracted from one are
            typically equivalent to persistence.
        '''
        return self.update(source=source, strength=strength, minimisation=minimisation, minimization=minimization, \
                           persistence=persistence, use_fitness=True)
    
    def update_rank(self, source, strength=0.1, persistence=0.9):
        '''Updates the pheromone map. This method is intended to be called directly
        from a system definition each generation.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          source : iterable(`Individual`)
            A sequence of individuals. The rankings of these individuals are used to
            increase pheromone levels.
          
          strength : float [defaults to 1.0]
            The multiplier to apply to ranks when adding to the pheromone value.
            
            The highest ranked individual adds this value to its pheromone trail and
            lower ranked individuals reduce this value linearly to one step before zero.
          
          persistence : |prob|
            The fraction of pheromone to retain on each update. Every pheromone value is
            multiplied by this value on each update. 'Decay' values subtracted from one are
            typically equivalent to persistence.
        '''
        return self.update(source=source, strength=strength, persistence=persistence, use_rank=True)
        
    def update(self, source, strength=1.0, minimisation=False, minimization=None, persistence=0.9, \
               use_fitness=True, use_rank=None):
        '''Updates the pheromone map. This method is intended to be called directly
        from a system definition each generation.
        
        .. include:: epydoc_include.txt
        
        :Parameters:
          source : iterable(`Individual`)
            A sequence of individuals. The fitness values or rankings of these individuals
            are used to increase pheromone levels.
          
          strength : float [defaults to 1.0]
            The multiplier to apply to fitness values or ranks when adding to the pheromone
            value.
            
            When using fitnesses, only the first part of the fitness value is used.
            Multi-part fitnesses should ensure that their first value is suitable for this
            use, or create a new pheromone map that can handle multiple parts correctly.
            The `esec.fitness.Fitness.simple` property is not used.
            
            When using ranks, the highest ranked individual adds this value to its
            pheromone trail and lower ranked individuals reduce this value linearly to one
            step before zero.
          
          minimisation : boolean [defaults to ``False``]
            If ``True``, the reciprocal of fitness values are used. If a lower fitness
            represents a better solution, this should be ``True`` to ensure a larger effect
            on the pheromone.
          
          minimization : boolean [defaults to ``False``]
            A synonym for `minimisation`. If specified, this value is used in preference to
            `minimisation`.
          
          persistence : |prob|
            The fraction of pheromone to retain on each update. Every pheromone value is
            multiplied by this value on each update. 'Decay' values subtracted from one are
            typically equivalent to persistence.
          
          use_fitness : boolean [defaults to ``True``]
            If ``True``, and `use_rank` is ``False`` or unspecified, uses fitness values to
            adjust pheromone.
          
          use_rank : boolean [defaults to ``False``]
            If ``True``, uses rankings to adjust pheromone.
        '''
        if use_rank != None: use_fitness = not use_rank
        if minimization != None: minimisation = minimization
        
        pheromone = self._pheromone
        
        for key in pheromone.iterkeys():
            pheromone[key] *= persistence

        # decay our initial value as well
        self.initial *= persistence
        initial = self.initial
        
        if use_fitness:
            for indiv in source:
                if minimisation:
                    delta = strength / float(indiv.fitness.values[0])
                else:
                    delta = strength * float(indiv.fitness.values[0])
                
                for p in indiv.phenome:
                    pheromone[p] = pheromone.get(p, initial) + delta
        else:
            # sort in worst-to-best fitness order
            group = sorted(source, key=lambda i: i.fitness)
            step = strength / len(group)
            delta = step
            
            for indiv in group:
                for p in indiv.phenome:
                    pheromone[p] = pheromone.get(p, initial) + delta
                delta += step
    
    
    def display(self):
        '''Displays the entire contents of this pheromone map.
        
        This is intended for debugging purposes only.
        '''
        items = sorted(self._pheromone.iteritems(), key=lambda i: i[0])
        result = []
        prev = items[0][0][0]
        for i in items:
            if i[0][0] != prev: print
            prev = i[0][0]
            print "%10s = %10.2f " % i,
        print
    
#==============================================================================

