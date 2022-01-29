import hdroller
import hdroller._die.base

from collections import defaultdict
import itertools

class MultiDie(hdroller._die.base.BaseDie):
    """Multivariate die.
    
    Outcomes are tuples, and operations are performed on each element of the tuples.
    """
    
    @property
    def is_single(self):
        """True iff this die is univariate."""
        return False
    
    def unary_op(self, op, *args):
        """Returns a die representing the effect of performing the operation on the outcomes."""
        data = defaultdict(int)
        for outcome, weight in self.items():
            new_outcome = tuple(op(x, *args) for x in outcome)
            data[new_outcome] += weight
        return hdroller.die(data)
    
    def binary_op(self, other, op, *args):
        """Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice."""
        data = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other, weight_other) in itertools.product(self.items(), other.items()):
            new_outcome = tuple(op(x, y, *args) for x, y in zip(outcome_self, outcome_other))
            data[new_outcome] += weight_self * weight_other
        return hdroller.die(data)
    
    @staticmethod
    def _getitem(self, outcome, i):
        # TODO: Advanced indexing.
        return outcome[i]
    
    def __getitem__(self, i):
        """Slices the outcomes of the die."""
        return self.unary_op(self._getitem, i)
    
    # Statistics.
    
    def covariance(self, i, j):
        return NotImplementedError("TODO")
    
    def correlation(self, i, j):
        return NotImplementedError("TODO")