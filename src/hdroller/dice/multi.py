import hdroller
import hdroller.dice.base
import hdroller.dice.single
import hdroller.indexing

from collections import defaultdict
import itertools

class MultiDie(hdroller.dice.base.BaseDie):
    """Multivariate die.
    
    Outcomes are tuples, and operations are performed on each element of the tuples.
    """
    
    def unary_op(self, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on the outcomes."""
        data = defaultdict(int)
        for outcome, weight in self.items():
            new_outcome = tuple(op(x, *args, **kwargs) for x in outcome)
            data[new_outcome] += weight
        return hdroller.die(data, ndim=self.ndim())
    
    def binary_op(self, other, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice."""
        ndim = self._check_ndim(other)
        data = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other, weight_other) in itertools.product(self.items(), other.items()):
            new_outcome = tuple(op(x, y, *args, **kwargs) for x, y in zip(outcome_self, outcome_other))
            data[new_outcome] += weight_self * weight_other
        return hdroller.die(data, ndim=ndim)
    
    def __getitem__(self, select):
        """Slices the dimensions of the die."""
        data = defaultdict(int)
        for outcome, weight in self.items():
            data[hdroller.indexing.select_from(outcome, select)] = weight
        ndim = sum(hdroller.indexing.select_bools(self.ndim(), select))
        return hdroller.die(data, ndim=ndim)
    
    # Statistics.
    
    def covariance(self, i, j):
        mean_i = self[i].mean()
        mean_j = self[j].mean()
        return sum((outcome[i] - mean_i) * (outcome[j] - mean_j) * weight for outcome, weight in self.items()) / self.total_weight()
    
    def correlation(self, i, j):
        sd_i = self[i].standard_deviation()
        sd_j = self[j].standard_deviation()
        return self.covariance(i, j) / (sd_i * sd_j)
