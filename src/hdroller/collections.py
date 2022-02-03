__docformat__ = 'google'

from functools import cached_property

class FrozenSortedWeights():
    """Immutable sorted dictionary whose values are integers.
    
    keys(), values(), and items() return tuples, which are subscriptable.
    """
    def __init__(self, d, trim=True):
        """
        Args:
            d: A dictionary of ints.
            trim: If True, zero weights will be omitted.
        """
        for key, value in d.items():
            if not isinstance(value, int):
                raise ValueError('Values must be ints, got ' + type(value).__name__)
            if value < 0:
                raise ValueError('Values must not be negative.')
        if trim:
            self._d = { k : d[k] for k in sorted(d.keys()) if d[k] > 0 }
            self._has_zero_weights = False
        else:
            self._d = { k : d[k] for k in sorted(d.keys()) }
            self._has_zero_weights = 0 in d.values()
    
    def has_zero_weights(self):
        """ Returns `True` iff `self` contains at least one zero weight. """
        return self._has_zero_weights
    
    def __len__(self):
        return len(self._d)
    
    def __contains__(self, key):
        return key in self._d
    
    def __getitem__(self, key):
        return self._d.get(key, 0)
        
    @cached_property
    def _keys(self):
        return tuple(self._d.keys())
    
    def keys(self):
        return self._keys
    
    @cached_property
    def _values(self):
        return tuple(self._d.values())
    
    def values(self):
        return self._values
    
    @cached_property
    def _items(self):
        return tuple(self._d.items())
    
    def items(self):
        return self._items
    
    def __len__(self):
        return len(self._d)

    def __str__(self):
        return str(self._d)
    
    def __repr__(self):
        return type(self).__qualname__ + f'({repr(self._d)})'