import hdroller
import hdroller.math
import numpy

class DieRepeater():
    """
    Class for computing statistics on repeated dice and caching intermediate information.
    In this file, "outcome"s are understood to always start from zero
    until constructing any output Die.
    """
    
    def __init__(self, die):
        self._die = die
        
        self.init_convolutions()
    
    def init_convolutions(self):
        """
        Fills convolutions with base cases.
        """
        
        """
        [num_dice]
        -> [outcome, num_eq_dice] 
        -> probability that num_dice will all be <= or => outcome
           with EXACTLY num_eq_dice equal to outcome_index.
        """
        conv_zero = numpy.ones((len(self._die), 0))
        leq_one = numpy.stack((self._die.cdf(inclusive=False), self._die.pmf()), axis=1)
        geq_one = numpy.stack((self._die.ccdf(inclusive=False), self._die.pmf()), axis=1)
        
        self._leq_exacts = [conv_zero, leq_one]
        self._geq_exacts = [conv_zero, geq_one]
        
        """
        [num_dice]
        -> [outcome, num_eq_dice]
        -> probability that num_dice will all be <= or => outcome
           with AT LEAST num_eq_dice equal to outcome_index.
        """
        self._leq_at_leasts = []
        self._geq_at_leasts = []
        
        """
        [num_dice]
        -> [outcome]
        -> probability that num_dice will all be < or > outcome.
        """
        self._lts = []
        self._gts = []
        
        """
        [num_dice]
        -> [outcome, sum]
        -> probability that num_dice will all be < or > outcome
           with the given sum.
        """
        conv_zero = numpy.ones((len(self._die), 1))
        full_one = numpy.tile(self._die.pmf(), (len(self._die), 1))

        lo_one = numpy.tril(full_one)
        hi_one = numpy.triu(full_one)
        
        self._lo_sums = [conv_zero, lo_one]
        self._hi_sums = [conv_zero, hi_one]
        
    @staticmethod
    def get_convolution(convolutions, num_dice):
        while len(convolutions) < num_dice+1:
            next = hdroller.math.convolve_along_axis(convolutions[-1], convolutions[1], axis=-1)
            convolutions.append(next)
        return convolutions[num_dice]
    
    def leq_exact(self, num_dice):
        return self.get_convolution(self._leq_exacts, num_dice)
        
    def geq_exact(self, num_dice):
        return self.get_convolution(self._geq_exacts, num_dice)
        
    @staticmethod
    def get_at_least(self, exacts, at_leasts, num_dice):
        while len(at_leasts) < num_dice+1:
            exact = self.get_convolution(exacts, len(at_leasts))
            next = hdroller.math.reverse_cumsum(exact, axis=1)
            at_leasts.append(next)
        return at_leasts(num_dice)
        
    def leq_at_least(self, num_dice):
        return self.get_at_least(self._leq_exacts, self._leq_at_leasts, num_dice)
    
    def geq_at_least(self, num_dice):
        return self.get_at_least(self._geq_exacts, self._geq_at_leasts, num_dice)
    
    @staticmethod
    def get_power(self, powers, base, num_dice):
        while len(powers) < num_dice+1:
            next = numpy.power(base, len(powers))
            powers.append(next)
        return powers[num_dice]
        
    def lt(self, num_dice):
        return self.get_power(self._lts, self._die.cdf(inclusive=False), num_dice)
    
    def gt(self, num_dice):
        return self.get_power(self._gts, self._die.ccdf(inclusive=False), num_dice)
        
    def lo_sum(self, num_dice):
        return self.get_convolution(self._lo_sums, num_dice)
        
    def hi_sum(self, num_dice):
        return self.get_convolution(self._hi_sums, num_dice)
        
    @staticmethod
    def keep_one_side(self, num_dice, num_keep, get_nonsum_at_least, get_sum):
        pmf_length = (num_dice - 1) * num_keep + 1
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
            for threshold in range(len(self._die)):
                nonsum_factor = get_nonsum_at_least(num_nonsum_dice)[threshold, num_kept_threshold_dice]
                sum_factor = get_sum(num_sum_dice)[threshold, :]
                partial_pmf = nonsum_factor * sum_factor * comb_factor
                partial_start = threshold * num_kept_threshold_dice
                pmf[partial_start:partial_start+len(partial_pmf)] += partial_pmf
        
        return hdroller.Die(pmf, min_outcome)
            
    def keep_highest(self, num_dice, num_keep):
        return self.keep_one_side(num_dice, num_keep, self.lo_at_least, self.hi_sum)
        
    def keep_lowest(self, num_dice, num_keep):
        return self.keep_one_side(num_dice, num_keep, self.hi_at_least, self.lo_sum)
        
    def keep_index(self, index):
        """
        Returns the indexth lowest die.
        """
        if index < 0: index = self._num_dice + index
        
        if index < self._num_dice // 2:
            short = self.lt
            long = self.geq_at_least
            min_long_dice = self._num_dice - index
        else:
            short = self.gt
            long = self.leq_at_least
            min_long_dice = index + 1
        
        pmf = numpy.zeros_like(self._die.pmf())
        min_outcome = self._die.min_outcome()
        # num_long_dice is the number of dice on the long side or equal to the selected index.
        for num_long_dice in range(min_long_dice, self._num_dice+1):
            num_short_dice = self._num_dice - num_long_dice
            comb_factor = hdroller.math.multinom(self._num_dice, (num_long_dice, num_short_dice))
            short_factor = short(num_short_dice)
            long_factor = long(num_long_dice)[:, num_long_dice - min_long_dice + 1]
            pmf += comb_factor * short_factor * long_factor
        
        return hdroller.Die(pmf, min_outcome) 