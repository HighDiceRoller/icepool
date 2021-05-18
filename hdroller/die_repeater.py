import hdroller
import hdroller.math
import hdroller.convolution_series
import hdroller.power_series

from functools import cached_property
import numpy

class DieRepeater():
    """
    Class for computing statistics on repeated dice and caching intermediate information.
    """
    
    def __init__(self, die):
        self._die = die
        
    @cached_property
    def _dice_lt_eq(self):
        """
        [num_dice]
        -> [face, num_eq_dice] 
        -> probability that num_dice will all be <= face
           with num_eq_dice equal to face.
        """
        lo_1 = numpy.stack((self._die.cdf(inclusive=False), self._die.pmf()), axis=1)
        return hdroller.convolution_series.ConvolutionSeries(lo_1)
        
    @cached_property
    def _dice_gt_eq(self):
        """
        [num_dice]
        -> [face, num_eq_dice] 
        -> probability that num_dice will all be >= face
           with num_eq_dice equal to face.
        """
        hi_1 = numpy.stack((self._die.ccdf(inclusive=False), self._die.pmf()), axis=1)
        return hdroller.convolution_series.ConvolutionSeries(hi_1)
    
    @cached_property
    def _dice_lt_sum(self):
        """
        [num_dice]
        -> [face, sum]
        -> probability that num_dice will all be < face
           with the given sum.
        """
        full_1 = numpy.tile(self._die.pmf(), (len(self._die), 1))
        lo_1 = numpy.tril(full_1, k=-1)
        return hdroller.convolution_series.ConvolutionSeries(lo_1)
    
    @cached_property
    def _dice_gt_sum(self):
        """
        [num_dice]
        -> [face, sum]
        -> probability that num_dice will all be > face
           with the given sum.
        """
        full_1 = numpy.tile(self._die.pmf(), (len(self._die), 1))
        hi_1 = numpy.triu(full_1, k=1)
        return hdroller.convolution_series.ConvolutionSeries(hi_1)
    
    @cached_property
    def _dice_lt(self):
        """
        [num_dice]
        -> [face]
        -> probability that num_dice will all be < face.
        """
        return hdroller.power_series.PowerSeries(self._die.cdf(inclusive=False))
        
    @cached_property
    def _dice_gt(self):
        """
        [num_dice]
        -> [face]
        -> probability that num_dice will all be > face.
        """
        return hdroller.power_series.PowerSeries(self._die.ccdf(inclusive=False))
        
    def keep_one_side(self, num_dice, num_keep, nonsum_convolutions, sum_convolutions):
        if num_keep == 0:
            """
            This special case exists because we assume there exists at least one lowest kept die,
            which isn't be the case if zero dice are kept.
            """
            return hdroller.Die(0)
        
        pmf_length = (len(self._die) - 1) * num_keep + 1
        pmf = numpy.zeros((pmf_length,))
        min_outcome = self._die.min_outcome() * num_keep
        
        # Let the "threshold" be the lowest or highest kept roll.
        # All dice inside the threshold are kept, all outside are dropped.
        # num_sum_dice is the number of dice inside of threshold.
        for num_sum_dice in range(0, num_keep):
            # num_nonsum_dice is the number of dice at or outside of threshold.
            num_nonsum_dice = num_dice - num_sum_dice
            # num_kept_threshold_dice is the number of kept dice == threshold.
            num_kept_threshold_dice = num_keep - num_sum_dice
            # The number of ways to assign each of num_dice to the sum or not.
            comb_factor = hdroller.math.multinom(num_dice, (num_nonsum_dice, num_sum_dice))
            nonsum_factor = nonsum_convolutions.reverse_cumsum(num_nonsum_dice)[:, num_kept_threshold_dice]
            sum_factor = sum_convolutions[num_sum_dice]
            partial_pmf = comb_factor * nonsum_factor[:, numpy.newaxis] * sum_factor
            partial_pmf_length = partial_pmf.shape[-1]
            for threshold in range(len(self._die)):
                partial_start = threshold * num_kept_threshold_dice
                pmf[partial_start:partial_start+partial_pmf_length] += partial_pmf[threshold, :]
        
        return hdroller.Die(pmf, min_outcome)
            
    def keep_highest(self, num_dice, num_keep):
        return self.keep_one_side(num_dice, num_keep, self._dice_lt_eq, self._dice_gt_sum)
        
    def keep_lowest(self, num_dice, num_keep):
        return self.keep_one_side(num_dice, num_keep, self._dice_gt_eq, self._dice_lt_sum)
        
    def keep_index(self, num_dice, index):
        """
        Returns the indexth lowest die.
        """
        if index < 0: index = num_dice + index
        
        if index < num_dice // 2:
            short = self._dice_lt
            long = self._dice_gt_eq
            min_long_dice = num_dice - index
        else:
            short = self._dice_gt
            long = self._dice_lt_eq
            min_long_dice = index + 1
        
        pmf = numpy.zeros_like(self._die.pmf())
        min_outcome = self._die.min_outcome()
        # num_long_dice is the number of dice on the long side or equal to the selected index.
        for num_long_dice in range(min_long_dice, num_dice+1):
            num_short_dice = num_dice - num_long_dice
            comb_factor = hdroller.math.multinom(num_dice, (num_long_dice, num_short_dice))
            short_factor = short[num_short_dice]
            long_factor = long.reverse_cumsum(num_long_dice)[:, num_long_dice - min_long_dice + 1]
            pmf += comb_factor * short_factor * long_factor
        
        return hdroller.Die(pmf, min_outcome) 