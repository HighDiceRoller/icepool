__docformat__ = 'google'

import hdroller
import hdroller.die.base
import hdroller.die.scalar

from collections import defaultdict
import itertools

class VectorDie(hdroller.die.base.BaseDie):
    """ Multivariate die.
    
    Outcomes are tuples and operators are performed elementwise.
    
    Statistical methods other than `mode()` take in an argument `i` specifying which dimension to take the statistic over.
    """
    
    def ndim(self):
        """ Returns the number of dimensions if is a `VectorDie`, or `False` otherwise. """
        return self._ndim
    
    def __init__(self, data, ndim):
        """ Constructor.
        
        Dice should not be constructed directly;
        instead, use one of the methods defined in `hdroller.die.func` 
        (which are imported into the top-level `hdroller` module).
        
        Args:
            data: A `Weights` mapping outcomes to weights.
            ndim: The number of dimensions of this die.
        """
        self._data = data
        self._ndim = ndim
    
    def unary_op(self, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation elementwise on the outcome sequences. """
        data = defaultdict(int)
        for outcome, weight in self.items():
            new_outcome = tuple(op(x, *args, **kwargs) for x in outcome)
            data[new_outcome] += weight
        return hdroller.Die(data, ndim=self.ndim())
    
    def binary_op(self, other, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation elementwise on pairs of outcome sequences from the two dice. """
        ndim = self.check_ndim(other)
        data = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other, weight_other) in itertools.product(self.items(), other.items()):
            new_outcome = tuple(op(x, y, *args, **kwargs) for x, y in zip(outcome_self, outcome_other))
            data[new_outcome] += weight_self * weight_other
        return hdroller.Die(data, ndim=ndim)
    
    def marginal(self, select):
        """ Returns the marginal distribution over selected dimensions of the die. """
        test_select = ([None] * self.ndim())[select]
        if hasattr(test_select, '__len__'):
            ndim = len(test_select)
        else:
            ndim = 1
        data = defaultdict(int)
        for outcome, weight in self.items():
            data[outcome[select]] += weight
        return hdroller.Die(data, ndim=ndim)
    
    __getitem__ = marginal
        
    
    # Statistics.
    # These apply to a single dimension `i`.
    
    def _apply_to_dim(self, func, i, *args, **kwargs):
        return func(self[i], *args, **kwargs)
    
    def median_left(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.median_left, i)
        
    def median_right(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.median_right, i)
    
    def median(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.median, i)
    
    def ppf_left(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.ppf_left, i)
        
    def ppf_right(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.ppf_right, i)
    
    def ppf(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.ppf, i)
        
    def mean(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.mean, i)
    
    def variance(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.variance, i)
    
    def standard_deviation(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.standard_deviation, i)
    
    sd = standard_deviation
    
    def standardized_moment(self, i, k):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.standardized_moment, i, k)
    
    def skewness(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.skewness, i)
        
    def excess_kurtosis(self, i):
        return self._apply_to_dim(hdroller.die.scalar.ScalarDie.excess_kurtosis, i)
    
    # Joint statistics.
    
    def covariance(self, i, j):
        mean_i = self[i].mean()
        mean_j = self[j].mean()
        return sum((outcome[i] - mean_i) * (outcome[j] - mean_j) * weight for outcome, weight in self.items()) / self.total_weight()
    
    def correlation(self, i, j):
        sd_i = self[i].standard_deviation()
        sd_j = self[j].standard_deviation()
        return self.covariance(i, j) / (sd_i * sd_j)
