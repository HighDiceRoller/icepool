__docformat__ = 'google'

import hdroller
import hdroller.die.base

class ZeroDie(hdroller.die.base.BaseDie):
    """ Die with with `ndim == 0`.
    
    This die produces no outcome information with 100% probability.
    This is distinct from having zero weight.
    
    Since there is no outcome information, operations do nothing.
    """
    
    def unary_op(self, op, *args, **kwargs):
        """ Since there is no outcome information, operations do nothing. """
        return self
    
    def binary_op(self, other, op, *args, **kwargs):
        """ Since there is no outcome information, operations do nothing. """
        ndim = self._check_ndim(other)
        return self
