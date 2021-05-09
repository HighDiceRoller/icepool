import hdroller
import hdroller.math
import numpy

from functools import cached_property

class PureDicePool():
    """
    Dice pool where all the dice are the same.
    Compared to MixedDicePool, this is considerably faster at dealing with large numbers of dice.
    """
    def __init__(self, num_dice, single_die):
        self._single_die = single_die
        self._num_dice = num_dice
        
        self._hi_sum_convolutions = []
    
    def single_len(self):
        return len(self._single_die)
        
    def single_min_outcome(self):
        return self._single_die.min_outcome()

    def _hi_or_lo_convolutions(self, cdf_or_ccdf):
        """
        Implementation of lo_convolutions and hi_convolutions.
        """
        result = numpy.zeros((self._num_dice+1, self.single_len(), self._num_dice+1))
        result[0, :, 0] = 1.0
        result[1, :, 0] = cdf_or_ccdf
        result[1, :, 1] = self._single_die.pmf()
        for num_hi_or_lo_dice in range(2, self._num_dice+1):
            for outcome_index in range(self.single_len()):
                recursive = result[num_hi_or_lo_dice-1, outcome_index, :num_hi_or_lo_dice]
                tail = result[1, outcome_index, :2]
                result[num_hi_or_lo_dice, outcome_index, :num_hi_or_lo_dice+1] = numpy.convolve(recursive, tail)
        
        """
        Convert from exactly num_*_eq_dice being == outcome_index
        to at least num_*_eq_dice being == outcome_index.
        """
        for num_hi_or_lo_dice in range(self._num_dice+1):
            pmfs = result[num_hi_or_lo_dice, :, :num_hi_or_lo_dice+1]
            result[num_hi_or_lo_dice, :, :num_hi_or_lo_dice+1] = numpy.flip(numpy.cumsum(numpy.flip(pmfs, axis=1), axis=1), axis=1)
        
        result.setflags(write=False)
        return result
    
    @cached_property
    def lo_convolutions(self):
        """
        An array that maps (num_lo_dice, outcome_index, num_lo_eq_dice) ->
        probability that num_lo_dice will all be <= outcome_index
        with at least num_lo_eq_dice being == outcome_index.
        """
        return self._hi_or_lo_convolutions(self._single_die.cdf(inclusive=False))
    
    @cached_property
    def lo_lt_convolutions(self):
        """
        An array that maps (num_lo_lt_dice, outcome_index) ->
        probability that num_lo_lt_dice will all be < outcome_index
        """
        result = self.lo_convolutions[:, :, 0]
        result = numpy.roll(result, 1, axis=1)
        result[1:, 0] = 0.0
        result.setflags(write=False)
        return result
    
    @cached_property
    def hi_convolutions(self):
        """
        An array that maps (num_hi_dice, outcome_index, num_hi_eq_dice) ->
        probability that num_hi_dice will all be >= outcome_index
        with at least num_hi_eq_dice being == outcome_index.
        """
        return self._hi_or_lo_convolutions(self._single_die.ccdf(inclusive=False))
    
    @cached_property
    def hi_gt_convolutions(self):
        """
        An array that maps (num_hi_gt_dice, outcome_index) ->
        probability that num_hi_gt_dice will all be > outcome_index.
        """
        result = self.hi_convolutions[:, :, 0]
        result = numpy.roll(result, -1, axis=1)
        result[1:, -1] = 0.0
        result.setflags(write=False)
        return result
    
    def hi_sum_convolution(self, num_sum_dice):
        """
        Returns an array that maps (outcome_index, sum) -> probability that num_sum_dice will all be strictly greater than outcome_index and have the given sum.
        """
        if num_sum_dice >= len(self._hi_sum_convolutions):
            if num_sum_dice == 0:
                result = numpy.ones((self.single_len(), 1))
            elif num_sum_dice == 1:
                result = numpy.zeros((self.single_len(), self.single_len()))
                for outcome_index in range(self.single_len()):
                    result[outcome_index, outcome_index+1:] = self._single_die.pmf()[outcome_index+1:]
            else:
                pmf_length = (self.single_len()-1) * num_sum_dice + 1
                result = numpy.zeros((self.single_len(), pmf_length))
                
                previous = self.hi_sum_convolution(num_sum_dice-1)
                one = self.hi_sum_convolution(1)
                for outcome_index in range(self.single_len()):
                    result[outcome_index, :] = numpy.convolve(previous[outcome_index, :], one[outcome_index, :])
            
            result.setflags(write=False)
            self._hi_sum_convolutions.append(result)
        return self._hi_sum_convolutions[num_sum_dice]
    
    def keep_highest(self, num_keep):
        if num_keep == 0: return hdroller.Die(0)
        
        pmf_length = (self.single_len()-1) * num_keep + 1
        pmf = numpy.zeros((pmf_length,))
        min_outcome = self.single_min_outcome() * num_keep
        
        # num_sum_dice is the number of dice > lo_outcome_index.
        for num_sum_dice in range(0, num_keep):
            # num_lo_dice is the number of dice <= lo_outcome_index.
            num_lo_dice = self._num_dice - num_sum_dice
            # num_lo_kept_dice is the number of kept dice == lo_outcome_index.
            num_lo_kept_dice = num_keep - num_sum_dice
            
            comb_factor = hdroller.math.multinom(self._num_dice, (num_lo_dice, num_sum_dice))
            # lo_outcome_index is the outcome index of the lowest kept die.
            for lo_outcome_index in range(self.single_len()):
                # lo_factor is the chance that num_lo_dice will all roll <= lo_outcome_index,
                # with at least num_lo_kept_dice being == lo_income_index.
                lo_factor = self.lo_convolutions[num_lo_dice, lo_outcome_index, num_lo_kept_dice]
                
                sum_factor = self.hi_sum_convolution(num_sum_dice)[lo_outcome_index, :]
                partial_pmf = lo_factor * sum_factor * comb_factor
                partial_outcome_start_index = lo_outcome_index * num_lo_kept_dice
                pmf[partial_outcome_start_index:partial_outcome_start_index+len(partial_pmf)] += partial_pmf
        
        return hdroller.Die(pmf, min_outcome)
    
    def keep_index(self, index):
        """
        Returns the indexth lowest die.
        """
        if index < 0: index = self._num_dice + index
        
        if index < self._num_dice // 2:
            short_convolutions = self.lo_lt_convolutions
            long_convolutions = self.hi_convolutions
            min_long_dice = self._num_dice - index
        else:
            short_convolutions = self.hi_gt_convolutions
            long_convolutions = self.lo_convolutions
            min_long_dice = index + 1
        
        pmf = numpy.zeros_like(self._single_die.pmf())
        min_outcome = self.single_min_outcome()
        # num_long_dice is the number of dice on the long side or equal to the selected index.
        for num_long_dice in range(min_long_dice, self._num_dice+1):
            num_short_dice = self._num_dice - num_long_dice
            comb_factor = hdroller.math.multinom(self._num_dice, (num_long_dice, num_short_dice))
            short_factor = short_convolutions[num_short_dice, :]
            long_factor = long_convolutions[num_long_dice, :, num_long_dice - min_long_dice + 1]
            pmf += comb_factor * short_factor * long_factor
        
        return hdroller.Die(pmf, min_outcome)
