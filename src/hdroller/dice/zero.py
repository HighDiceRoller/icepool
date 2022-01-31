__docformat__ = 'google'

import hdroller
import hdroller.dice.base

class ZeroDie(hdroller.dice.base.BaseDie):
    """ Die with with `ndim == 0`.
    
    The only possible outcome is the empty tuple `()`.
    
    Since there is no outcome information, operations do nothing.
    """
    
    def unary_op(self, op, *args, **kwargs):
        """ Since there is no outcome information, operations do nothing. """
        return self
    
    def binary_op(self, other, op, *args, **kwargs):
        """ Since there is no outcome information, operations do nothing. """
        ndim = self._check_ndim(other)
        return self
