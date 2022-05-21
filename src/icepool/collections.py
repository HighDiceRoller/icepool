__docformat__ = 'google'

import icepool

from functools import cached_property
import math


class Counts():
    """Immutable dictionary whose values are integers.

    keys(), values(), and items() return tuples, which are subscriptable.
    """

    def __init__(self, items):
        """
        Args:
            items: A sequence of key, value pairs.
        """
        for key, value in items:
            if key is None:
                raise TypeError('None is not a valid outcome.')
            if isinstance(key, icepool.SpecialValue):
                raise TypeError(str(key) + ' is not a valid outcome.')
            if not isinstance(value, int):
                raise ValueError('Values must be ints, got ' +
                                 type(value).__name__)

        self._d = {k: v for k, v in items}

    @cached_property
    def _has_zero_weights(self):
        return 0 in self.values()

    def has_zero_weights(self):
        """Returns `True` iff `self` contains at least one zero weight. """
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

    def __str__(self):
        return str(self._d)

    def __repr__(self):
        return type(self).__qualname__ + f'({repr(self._d)})'

    def reduce(self):
        """Divides all counts by their greatest common denominator."""
        gcd = math.gcd(*self.values())
        if gcd <= 1:
            return self
        data = [(outcome, weight // gcd) for outcome, weight in self.items()]
        return Counts(data)
