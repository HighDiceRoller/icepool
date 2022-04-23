__docformat__ = 'google'

import icepool
from icepool.collections import Counts

from collections import defaultdict
from functools import cached_property

def _is_dict(arg):
    return hasattr(arg, 'keys') and hasattr(arg, 'items') and hasattr(arg, '__getitem__')

class PoolRoll(icepool.BasePool):
    """ Represents a single, fixed roll of a dice pool.
    
    Like `DicePool`, this may be used as an argument to `EvalPool`.
    """
    def __init__(self, *args):
        """
        Args:
            *args: A sequence of:
                * Dict-likes, mapping outcomes to counts.
                * Outcomes, which are treated as having count 1.
                Duplicate outcomes will have their counts accumulated.
        """
        data = defaultdict(int)
        for arg in args:
            if _is_dict(arg):
                for key, value in arg.items():
                    data[key] += value
            else:
                data[arg] += 1
        
        self._data = Counts(data)

    def _is_single_roll(self):
        return True
    
    def _has_max_outcomes(self):
        return False
    
    def _has_min_outcomes(self):
        return False
    
    def outcomes(self):
        return self._data.keys()
    
    def _max_outcome(self):
        return self._data.keys()[-1]
    
    def _min_outcome(self):
        return self._data.keys()[0]
    
    def _pop_max(self):
        data = { outcome : count for outcome, count in self._data.items()[:-1] }
        count = self._data.values()[-1]
        return (PoolRoll(data), count, 1),
    
    def _pop_min(self):
        data = { outcome : count for outcome, count in self._data.items()[1:] }
        count = self._data.values()[0]
        return (PoolRoll(data), count, 1),
    
    # Forwarding dict-like methods.
    
    def keys(self):
        return self._data.keys()
        
    def items(self):
        return self._data.items()
    
    def __getitem__(self, key):
        return self._data[key]

    def __str__(self):
        return f'PoolRoll({str(self._data)})'
    
    @cached_property
    def _key_tuple(self):
        return self._data.items()
    
    def __eq__(self, other):
        try:
            other = icepool.PoolRoll(other)
        except ValueError:
            return False
        return self._key_tuple == other._key_tuple
    
    @cached_property
    def _hash(self):
        return hash(self._key_tuple)
        
    def __hash__(self):
        return self._hash
