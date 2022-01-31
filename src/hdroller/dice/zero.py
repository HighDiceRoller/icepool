__docformat__ = 'google'

import hdroller
import hdroller.dice.base

class ZeroDie(hdroller.dice.base.BaseDie):
    """ Die with with `ndim == 0`.
    
    The only possible outcome is the empty tuple `()`.
    """
    
    def unary_op(self, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on the outcomes."""
        return self
    
    def binary_op(self, other, op, *args, **kwargs):
        """Returns a die representing the effect of performing the operation on pairs of outcomes from the two dice."""
        ndim = self._check_ndim(other)
        return self
