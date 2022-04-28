__docformat__ = 'google'

import icepool
import icepool.die.base
from icepool.collections import Counts

class EmptyDie(icepool.die.base.BaseDie):
    """ Die with no outcomes. """
    
    def ndim(self):
        return icepool.Empty
    
    def __init__(self):
        """ Constructor.
        
        Dice should not be constructed directly;
        instead, use one of the methods defined in `icepool.die.func` 
        (which are imported into the top-level `icepool` module).
        """
        self._data = Counts({})
        
    def _unary_op(self, op, *args, **kwargs):
        """ There are no outcomes, so nothing happens. """
        return self
    
    def _binary_op(self, other, op, *args, **kwargs):
        """ There are no outcomes, so nothing happens. """
        return self
    
    def _wrap_unpack(self, func):
        return func

    def __repr__(self):
        return type(self).__qualname__ + '()'
    
    def markdown(self, include_weights=True):
        return 'EmptyDie'
