from functools import cached_property

class FrozenSortedDict():
    """Immutable sorted dictionary whose values are integers.
    
    keys(), values(), and items() return tuples, which are subscriptable.
    """
    def __init__(self, d):
        """Constructor with no checking.
        
        Args:
            d: A dictionary of integers, sorted by keys.
                This should already be sorted.
                This should already have zeros filtered out, if desired.
        """
        self._d = d
    
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
    
    def pop_min(self):
        """Returns a copy of self with the min key removed, the popped key, and the popped value.
        
        Returns None, None, 0 if self has no elements remaining.
        """
        if len(self) > 0:
            return FrozenSortedDict({ k : v for k, v in zip(self._keys[1:], self._values[1:]) }), self._keys[0], self._values[0]
        else:
            return None, None, 0
    
    def pop_max(self):
        """Returns a copy of self with the max key removed, the popped key, and the popped value.
        
        Returns None, None, 0 if self has no elements remaining.
        """
        if len(self) > 0:
            return FrozenSortedDict({ k : v for k, v in zip(self._keys[:-1], self._values[:-1]) }), self._keys[-1], self._keys[-1]
        else:
            return None, None, 0

    def __str__(self):
        return str(self._d)
    
    def __repr__(self):
        return type(self).__name__ + f'({repr(self._d)})'