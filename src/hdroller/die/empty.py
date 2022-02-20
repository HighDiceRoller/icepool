__docformat__ = 'google'

import hdroller
import hdroller.die.base
from hdroller.collections import Weights

class EmptyDie(hdroller.die.base.BaseDie):
    """ Die with no outcomes. """
    
    def ndim(self):
        """ Returns the number of dimensions if this is a `VectorDie`.
        
        Otherwise, returns 'scalar' for a `ScalarDie` and 'empty'` for an `EmptyDie`.
        """
        return 'empty'
    
    def __init__(self):
        self._data = Weights({})
        
    def unary_op(self, op, *args, **kwargs):
        """ There are no outcomes, so nothing happens. """
        return self
    
    def binary_op(self, other, op, *args, **kwargs):
        """ There are no outcomes, so nothing happens. """
        return self
    
    def wrap_unpack(self, func):
        """ Possibly wraps func so that outcomes are unpacked before giving it to func. """
        return func

    def __repr__(self):
        return type(self).__qualname__ + '()'
    
    def __str__(self):
        return 'EmptyDie'
