__docformat__ = 'google'

import icepool
import icepool.die.base
from icepool.collections import Slicer

from collections import defaultdict
from functools import cached_property, wraps
import itertools

class VectorDie(icepool.die.base.BaseDie):
    """ Multivariate die.
    
    Outcomes are tuples. Most methods and operators are performed elementwise.
    Methods that depend on a flat outcome order use tuple order.
    
    Statistical methods other than `mode()` take in an argument `i` specifying which dimension to take the statistic over.
    """
    
    def ndim(self):
        return self._ndim
    
    def __init__(self, data, ndim):
        """ Constructor.
        
        Dice should not be constructed directly;
        instead, use one of the methods defined in `icepool.die.func` 
        (which are imported into the top-level `icepool` module).
        
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
        return icepool.Die(data, ndim=self.ndim())
    
    def binary_op(self, other, op, *args, **kwargs):
        """ Returns a die representing the effect of performing the operation elementwise on pairs of outcome sequences from the two dice. """
        data = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other, weight_other) in itertools.product(self.items(), other.items()):
            new_outcome = tuple(op(x, y, *args, **kwargs) for x, y in zip(outcome_self, outcome_other))
            data[new_outcome] += weight_self * weight_other
        return icepool.Die(data, ndim=self.ndim())
    
    def wrap_unpack(self, func):
        @wraps(func)
        def unpacked_func(outcome):
            return func(*outcome)
        return unpacked_func
    
    def marginal(self, select):
        """ Returns the marginal distribution over selected dimensions of the die. """
        test_select = ([None] * self.ndim())[select]
        if hasattr(test_select, '__len__'):
            ndim = len(test_select)
        else:
            ndim = 'scalar'
        data = defaultdict(int)
        for outcome, weight in self.items():
            data[outcome[select]] += weight
        return icepool.Die(data, ndim=ndim)
    
    @cached_property
    def dim(self):
        """ Subscript this to produce a marginal distribution.
        
        For example, `die.dim[0]` will extract the 0th dimension.
        """
        return Slicer(self.marginal)
    
    def all(self):
        """ Returns a die representing whether all dimensions are true. """
        return self.sub(lambda *outcome: all(outcome), ndim='scalar')
    
    def any(self):
        """ Returns a die representing whether any dimension is true. """
        return self.sub(lambda *outcome: any(outcome), ndim='scalar')
    
    # Statistics.
    # These apply to a single dimension `i`.
    
    def _apply_to_dim(self, func, i, *args, **kwargs):
        return func(self[i], *args, **kwargs)
    
    def median_left(self, i):
        return self._apply_to_dim(icepool.ScalarDie.median_left, i)
        
    def median_right(self, i):
        return self._apply_to_dim(icepool.ScalarDie.median_right, i)
    
    def median(self, i):
        return self._apply_to_dim(icepool.ScalarDie.median, i)
    
    def ppf_left(self, i):
        return self._apply_to_dim(icepool.ScalarDie.ppf_left, i)
        
    def ppf_right(self, i):
        return self._apply_to_dim(icepool.ScalarDie.ppf_right, i)
    
    def ppf(self, i):
        return self._apply_to_dim(icepool.ScalarDie.ppf, i)
        
    def mean(self, i):
        return self._apply_to_dim(icepool.ScalarDie.mean, i)
    
    def variance(self, i):
        return self._apply_to_dim(icepool.ScalarDie.variance, i)
    
    def standard_deviation(self, i):
        return self._apply_to_dim(icepool.ScalarDie.standard_deviation, i)
    
    sd = standard_deviation
    
    def standardized_moment(self, i, k):
        return self._apply_to_dim(icepool.ScalarDie.standardized_moment, i, k)
    
    def skewness(self, i):
        return self._apply_to_dim(icepool.ScalarDie.skewness, i)
        
    def excess_kurtosis(self, i):
        return self._apply_to_dim(icepool.ScalarDie.excess_kurtosis, i)
    
    # Joint statistics.
    
    def covariance(self, i, j):
        mean_i = self[i].mean()
        mean_j = self[j].mean()
        return sum((outcome[i] - mean_i) * (outcome[j] - mean_j) * weight for outcome, weight in self.items()) / self.denominator()
    
    def correlation(self, i, j):
        sd_i = self[i].standard_deviation()
        sd_j = self[j].standard_deviation()
        return self.covariance(i, j) / (sd_i * sd_j)
    
    def __repr__(self):
        return type(self).__qualname__ + f'({self._data.__repr__()}, ndim={self.ndim()})'
    
    def markdown(self, include_weights=True):
        """ Formats the die as a Markdown table. """
        outcome_lengths = []
        for i in range(self.ndim()):
            outcome_length = max(tuple(len(str(outcome[i])) for outcome in self.outcomes()) + (len(f'Outcome[{i}]'),))
            outcome_lengths.append(outcome_length)
        result = ''
        result += f'Denominator: {self.denominator()}\n\n'
        result += '|'
        for i in range(self.ndim()):
            result += ' ' + ' ' * (outcome_lengths[i] - len(f'Outcome[{i}]')) + f'Outcome[{i}]' + ' |'
        if include_weights:
            weight_length = max(tuple(len(str(weight)) for weight in self.weights()) + (len('Weight'),))
            result += ' ' + ' ' * (weight_length - len('Weight')) + 'Weight |'
        if self.denominator() > 0:
            result += ' Probability |'
        result += '\n'
        result += '|'
        for i in range(self.ndim()):
            result += '-' + '-' * outcome_lengths[i] + ':|'
        if include_weights:
            result += '-' + '-' * weight_length + ':|'
        if self.denominator() > 0:
            result += '------------:|'
        result += '\n'
        for outcome, weight, p in zip(self.outcomes(), self.weights(), self.pmf()):
            result += '|'
            for i, x in enumerate(outcome):
                result += f' {str(x):>{outcome_lengths[i]}} |'
            if include_weights:
                result += f' {weight:>{weight_length}} |'
            if self.denominator() > 0:
                result += f' {p:11.6%} |'
            result += '\n'
        return result
