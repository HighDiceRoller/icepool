import hdroller
import hdroller.die_base

from collections import defaultdict
import itertools

class DieSingle(hdroller.die_base.DieBase):
    """Univariate die.
    
    Operations are performed directly on the outcomes.
    """
    
    @property
    def is_multi(self):
        """True iff this die is multivariate."""
        return False
    
    def unary_op(self, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on the outcomes."""
        data = defaultdict(int)
        for outcome, weight in self.items():
            data[op(outcome, *args, **kwargs)] += weight
        return hdroller.die(data)
    
    def binary_op(self, other, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice."""
        data = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other, weight_other) in itertools.product(self.items(), other.items()):
            data[op(outcome_self, outcome_other, *args, **kwargs)] += weight_self * weight_other
        return hdroller.die(data)
