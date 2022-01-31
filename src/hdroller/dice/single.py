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
    
    def median(self):
        """ Returns the median. 
        
        If the median lies between two outcomes, returns the sum of the two / 2.
        """
        left_index = bisect.bisect_left(self.cweights(), self.total_weight() / 2)
        right_index = bisect.bisect_right(self.cweights(), self.total_weight() / 2)
        return (self.outcomes()[left_index] + self.outcomes()[right_index]) / 2
    
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
        Produces a MultiDie from the cartesian product of the input SingleDie.
        
        Args:
            *dice: Multiple dice or a single iterable of dice.
        
        Raises:
            TypeError if any of the input dice are already MultiDie.
        """
        if any(die.ndim > 1 for die in dice):
            raise TypeError('cartesian_product() is only valid on SingleDie.')
        
        data = defaultdict(int)
        for t in itertools.product(*(die.items() for die in dice)):
            outcomes, weights = zip(*t)
            data[outcomes] += math.prod(weights)
        
        return hdroller.die(data)
