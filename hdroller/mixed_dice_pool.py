import hdroller
import numpy

class MixedDicePool():
    def __init__(self, *dice):
        self._dice = hdroller.Die._union_outcomes(*dice)
        
        self._pmfs = [die.pmf() for die in self._dice]
        
        # (die_indexes, is_inclusives) -> product of cdfs
        self._cdf_product_cache = {}
        
        # (die_indexes, outcome_start_indexes, outcome_end_indexes) -> convolution
        self._convolution_cache = {}
        
    def single_min_outcome(self):
        return self._dice[0].min_outcome()
        
    def single_max_outcome(self):
        return self._dice[0].max_outcome()
    
    def single_len(self):
        return len(self._dice[0])
        
    """
    Helper methods to compute and cache intermediate results.
    
    While for a single computation it's possible to arrange the recursion so that
    all partial results are stored only on the stack, caching simplifies the code
    and allows reuse for later calls.
    """
    
    def cdf_product(self, die_indexes, is_inclusives):
        """
        Returns the chance of the dice with the given indices all rolling < or <=
        each outcome index. < or <= is determined for each die by is_inclusives.
        die_indexes should be a tuple in sorted order. 
        is_inclusives should be a tuple with one boolean per die_index.
        """
        
        key = (die_indexes, is_inclusives)
        if key not in self._cdf_product_cache:
            tail_die_index = die_indexes[-1]
            tail_is_inclusive = is_inclusives[-1]
            
            if len(die_indexes) == 1:
                result = self._dice[tail_die_index].cdf(inclusive=tail_is_inclusive)
            else:
                tail_result = self.cdf_product((tail_die_index,), (tail_is_inclusive,))
                recursive_result = self.cdf_product(die_indexes[:-1], is_inclusives[:-1])
                result = recursive_result * tail_result
            
            self._cdf_product_cache[key] = result
        return self._cdf_product_cache[key]
    
    def convolution(self, die_indexes, outcome_start_indexes=None, outcome_end_indexes=None):
        if outcome_start_indexes is None: outcome_start_indexes = (0,) * len(die_indexes)
        if outcome_end_indexes is None: outcome_end_indexes = (self.single_len(),) * len(die_indexes)
        
        key = (die_indexes, outcome_start_indexes, outcome_end_indexes)
        if key not in self._convolution_cache:
            if len(die_indexes) == 0:
                return numpy.array([1.0])
            
            tail_die_index = die_indexes[-1]
            tail_outcome_start_index = outcome_start_indexes[-1]
            tail_outcome_end_index = outcome_end_indexes[-1]
            
            if len(die_indexes) == 1:
                result = self._pmfs[tail_die_index][tail_outcome_start_index:tail_outcome_end_index]
            else:
                tail_result = self.convolution((tail_die_index,), (tail_outcome_start_index,), (tail_outcome_end_index,))
                if len(tail_result) == 0:
                    result = numpy.zeros((0,))
                else:
                    recursive_result = self.convolution(die_indexes[:-1], outcome_start_indexes[:-1], outcome_end_indexes[:-1])
                    if len(recursive_result) == 0:
                        result = numpy.zeros((0,))
                    else:
                        result = numpy.convolve(recursive_result, tail_result)
            
            self._convolution_cache[key] = result
        return self._convolution_cache[key]
    
    def keep_highest(self, num_keep):
        num_drop = len(self._dice) - num_keep
    
        pmf_length = (self.single_len()-1) * num_keep + 1
        pmf = numpy.zeros((pmf_length,))
        min_outcome = self.single_min_outcome() * num_keep
        
        def keep_highest_inner(current_die_index=0, dropped_die_indexes=(), lo_die_index=None, upper_die_indexes=()):
            if current_die_index < len(self._dice):
                if len(dropped_die_indexes) < num_drop:
                    keep_highest_inner(current_die_index+1, dropped_die_indexes + (current_die_index,), lo_die_index, upper_die_indexes)
                if lo_die_index is None:
                    keep_highest_inner(current_die_index+1, dropped_die_indexes, current_die_index, upper_die_indexes)
                if len(upper_die_indexes) < num_keep-1:
                    keep_highest_inner(current_die_index+1, dropped_die_indexes, lo_die_index, upper_die_indexes + (current_die_index,))
            else:
                lo_pmf = self.cdf_product(dropped_die_indexes, tuple(index > lo_die_index for index in dropped_die_indexes)) * self._pmfs[lo_die_index]
                for lo_outcome_index, lo_mass in enumerate(lo_pmf):
                    is_exclusives = numpy.array(upper_die_indexes) > lo_die_index
                    outcome_start_indexes = is_exclusives + lo_outcome_index

                    partial_pmf = lo_mass * self.convolution(upper_die_indexes, tuple(outcome_start_indexes))
                    partial_outcome_start_index = lo_outcome_index + numpy.sum(outcome_start_indexes)
                    
                    pmf[partial_outcome_start_index:partial_outcome_start_index+len(partial_pmf)] += partial_pmf
        
        keep_highest_inner()
        
        return hdroller.Die(pmf, min_outcome)._trim()