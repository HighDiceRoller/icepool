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
    
    # Special operators.
    
    def d(self, other):
        """ Roll the left die, then roll the right die that many times and sum the outcomes. 
        
        If an `int` is provided for the right side, it becomes a standard die with that many faces.
        Otherwise it is cast to a die.
        """
        if isinstance(other, int):
            other = hdroller.standard(other)
        else:
            other = hdroller.die(other)
        
        subresults = []
        subresult_weights = []
        
        max_abs_die_count = max(abs(self.min_outcome()), abs(self.max_outcome()))
        for die_count, die_count_weight in self.items():
            factor = other.total_weight() ** (max_abs_die_count - abs(die_count))
            subresults.append(other.repeat_and_sum(die_count))
            subresult_weights.append(die_count_weight * factor)
        
        subresults = hdroller.align(*subresults)
        
        data = defaultdict(int)
        
        for subresult, subresult_weight in zip(subresults, subresult_weights):
            for outcome, weight in subresult.items():
                data[outcome] += weight * subresult_weight
            
        return hdroller.die(data, ndim=other.ndim())
    
    def __matmul__(self, other):
        """ Roll the left die, then roll the right die that many times and sum the outcomes. 
        
        Unlike other operators, this does not work for built-in types on the right side.
        For example, `1 @ 6` does not work, nor does `d(6) @ 6`. But `1 @ d(6)` works.
        
        This is because all other operators convert their right side to a die using die,
        so `6` would become a constant 6, while  `d()` converts `int`s to a standard die with that many sides,
        so `6` would become a d6. Thus the right-side conversion of `@` would be ambiguous.
        """
        if not isinstance(other, hdroller.dice.base.BaseDie):
            raise TypeError(f'The @ operator will not automatically convert the right side of type {type(other).__qualname__} to a die.')
        return self.d(other)
    
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
        """ Returns a quantile, `n / d` of the way through the cdf.
        
        If the result lies between two outcomes, returns the lower of the two.
        """
        index = bisect.bisect_left(self.cweights(), (n * self.total_weight() + d - 1) // d)
        if index >= len(self): return self.max_outcome()
        return self.outcomes()[index]
    
    def ppf_right(self, n, d=100):
        """ Returns a quantile, `n / d` of the way through the cdf.
        
        If the result lies between two outcomes, returns the higher of the two.
        """
        index = bisect.bisect_right(self.cweights(), n * self.total_weight() // d)
        if index >= len(self): return self.max_outcome()
        return self.outcomes()[index]
    
    def ppf(self, n, d=100):
        """ Returns a quantile, `n / d` of the way through the cdf.
        
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
