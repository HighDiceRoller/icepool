import hdroller
import hdroller._die.base
import hdroller._die.multi

from collections import defaultdict
import itertools
import math

class SingleDie(hdroller._die.base.BaseDie):
    """Univariate die.
    
    Operations are performed directly on the outcomes.
    """
    
    def is_single(self):
        """True iff this die is univariate."""
        return True
    
    def unary_op(self, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on the outcomes."""
        data = defaultdict(int)
        for outcome, weight in self.items():
            data[op(outcome, *args, **kwargs)] += weight
        return hdroller.die(data, force_single=True)
    
    def binary_op(self, other, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice."""
        data = defaultdict(int)
        for (outcome_self, weight_self), (outcome_other, weight_other) in itertools.product(self.items(), other.items()):
            data[op(outcome_self, outcome_other, *args, **kwargs)] += weight_self * weight_other
        return hdroller.die(data, force_single=True)
    
    def cartesian_product(*dice):
        """
        Produces a MultiDie from the cartesian product of the input SingleDie.
        
        Args:
            *dice: Multiple dice or a single iterable of dice.
        
        Raises:
            TypeError if any of the input dice are already MultiDie.
        """
        dice = hdroller._die.base._listify_dice(dice)
        
        if any(not die.is_single() for die in dice):
            raise TypeError('cartesian_product() is only valid on SingleDie.')
        
        data = defaultdict(int)
        for t in itertools.product(*(die.items() for die in dice)):
            outcomes, weights = zip(*t)
            data[outcomes] += math.prod(weights)
        
        return hdroller.die(data)

    def __repr__(self):
        return type(self).__name__ + f'({self._data.__repr__()})'