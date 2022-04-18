__docformat__ = 'google'

import icepool

from collections import defaultdict
from icepool.collections import Weights

def _is_dict(arg):
    return hasattr(arg, 'keys') and hasattr(arg, 'items') and hasattr(arg, '__getitem__')

class PoolRoll(icepool.BasePool):
    """ Represents a single, fixed roll of a dice pool.
    
    Like `DicePool`, this may be used as an argument to `EvalPool`.
    """
    def __init__(self, *args, die=None):
        """
        Args:
            *args: A sequence of:
                * Dict-likes, mapping outcomes to counts.
                * Outcomes, with count 1.
                Duplicate outcomes will have their counts accumulated.
            die: If provided, all args must be outcomes within this die,
                and any outcomes within this die that are not provided will be set to zero count.
        """
        data = defaultdict(int)
        for arg in args:
            if _is_dict(arg):
                for key, value in arg.items():
                    data[key] += value
            else:
                data[arg] += 1
        
        if die is not None:
            for outcome in data.keys():
                if outcome not in die:
                    raise ValueError(f'Outcome {outcome} is not present in provided die.')
            for outcome in die.outcomes():
                data[outcome] += 0
        
        self._data = Weights(data)

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

    def __str__(self):
        return f'PoolRoll({str(self._data)})'
