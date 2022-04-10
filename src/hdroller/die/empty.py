__docformat__ = 'google'

import hdroller
import hdroller.die.base
from hdroller.collections import Weights

class EmptyDie(hdroller.die.base.BaseDie):
    """ Die with no outcomes. """
    
    def ndim(self):
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
        return func

    def __repr__(self):
        return type(self).__qualname__ + '()'
    
    def markdown(self, include_weights=True):
        return 'EmptyDie'
