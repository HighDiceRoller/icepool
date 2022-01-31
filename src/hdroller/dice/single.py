__docformat__ = 'google'

import hdroller
import hdroller.dice.base
import hdroller.dice.multi

import bisect
from collections import defaultdict
import itertools
import math

class SingleDie(hdroller.dice.base.BaseDie):
    """ Univariate die with `ndim == 1`.
    
    Operations are performed directly on the outcomes.
    
    Statistics have an extra parameter `i` specifying a single dimension to take the statistic over.
    """
    
    def unary_op(self, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation on the outcomes. """
        data = defaultdict(int)
        for outcome, weight in self.items():
            data[op(outcome, *args, **kwargs)] += weight
        return hdroller.die(data, ndim=1)
    
    def binary_op(self, other, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice. """
        ndim = self._check_ndim(other)
        data = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other, weight_other) in itertools.product(self.items(), other.items()):
            data[op(outcome_self, outcome_other, *args, **kwargs)] += weight_self * weight_other
        return hdroller.die(data, ndim=1)
    
    # Statistics.
    
    def median_left(self):
        """ Returns the median.
        
        If the median lies between two outcomes, returns the lower of the two. """
        return self.ppf_left(1, 2)
    
    def median_right(self):
        """ Returns the median.
        
        If the median lies between two outcomes, returns the higher of the two. """
        return self.ppf_right(1, 2)
    
    def median(self):
        """ Returns the median.
        
        If the median lies between two outcomes, returns the mean of the two.
        This will fail if the outcomes do not support division;
        in this case, use `median_left` or `median_right` instead.
        """
        return self.ppf(1, 2)
    
    def ppf_left(self, n, d=100):
        """ Returns a quantile, n / d of the way through the cdf.
        
        If the result lies between two outcomes, returns the lower of the two.
        """
        index = bisect.bisect_left(self.cweights(), (n * self.total_weight() + d - 1) // d)
        if index >= len(self): return self.max_outcome()
        return self.outcomes()[index]
    
    def ppf_right(self, n, d=100):
        """ Returns a quantile, n / d of the way through the cdf.
        
        If the result lies between two outcomes, returns the higher of the two.
        """
        index = bisect.bisect_right(self.cweights(), n * self.total_weight() // d)
        if index >= len(self): return self.max_outcome()
        return self.outcomes()[index]
    
    def ppf(self, n, d=100):
        """ Returns a quantile, n / d of the way through the cdf.
        
        If the result lies between two outcomes, returns the mean of the two.
        This will fail if the outcomes do not support division;
        in this case, use `ppf_left` or `ppf_right` instead.
        """
        return (self.ppf_left(n, d) + self.ppf_right(n, d)) / 2
    
    def mean(self):
        return sum(outcome * p for outcome, p in zip(self.outcomes(), self.pmf()))
    
    def variance(self):
        mean = self.mean()
        mean_of_squares = sum(p * outcome ** 2 for outcome, p in zip(self.outcomes(), self.pmf()))
        return mean_of_squares - mean * mean
    
    def standard_deviation(self):
        return math.sqrt(self.variance())
    
    sd = standard_deviation
    
    def standardized_moment(self, k):
        sd = self.standard_deviation()
        mean = self.mean()
        ev = sum(p * (outcome - mean) ** k for outcome, p in zip(self.outcomes(), self.pmf()))
        return ev / (sd ** k)
    
    def skewness(self):
        return self.standardized_moment(3.0)
    
    def excess_kurtosis(self):
        return self.standardized_moment(4.0) - 3.0
    
    def cartesian_product(*dice):
        """
        Produces a `MultiDie` from the Cartesian product of the input `SingleDie`.
        
        This is usually not recommended, as it takes space and time exponential in the number of dice,
        while not actually producing any additional information.
        
        Args:
            *dice: Multiple dice or a single iterable of dice.
        
        Raises:
            `TypeError` if any of the input dice are already `MultiDie`.
        """
        if any(die.ndim > 1 for die in dice):
            raise TypeError('cartesian_product() is only valid on SingleDie.')
        
        data = defaultdict(int)
        for t in itertools.product(*(die.items() for die in dice)):
            outcomes, weights = zip(*t)
            data[outcomes] += math.prod(weights)
        
        return hdroller.die(data)
