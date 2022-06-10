__docformat__ = 'google'

import icepool

from functools import cached_property
import math

from collections.abc import ItemsView, Iterator, KeysView, Mapping, Sequence, ValuesView
from typing import Any


class Counts(Mapping[Any, int]):
    """Immutable dictionary whose values are integers.

    keys(), values(), and items() return tuples, which are subscriptable.
    """

    def __init__(self, items: Sequence[tuple[Any, int]]):
        """
        Args:
            items: A sequence of key, value pairs.
        """
        self._d = {}
        for key, value in items:
            if key is None:
                raise TypeError('None is not a valid key.')
            if isinstance(key, icepool.SpecialValue):
                raise TypeError(str(key) + ' is not a valid key.')
            if not isinstance(value, int):
                raise ValueError('Values must be ints, got ' +
                                 type(value).__name__)
            self._d[key] = value

    @cached_property
    def _has_zero_values(self):
        return 0 in self.values()

    def has_zero_values(self) -> bool:
        """Returns `True` iff `self` contains at least one zero weight. """
        return self._has_zero_values

    def __len__(self) -> int:
        return len(self._d)

    def __contains__(self, key) -> bool:
        return key in self._d

    def __getitem__(self, key) -> int:
        return self._d.get(key, 0)

    def __iter__(self) -> Iterator:
        return iter(self._d)

    @cached_property
    def _keys(self):
        return tuple(self._d.keys())

    def keys(self) -> 'CountsKeysView':
        return CountsKeysView(self)

    @cached_property
    def _values(self):
        return tuple(self._d.values())

    def values(self) -> 'CountsValuesView':
        return CountsValuesView(self)

    @cached_property
    def _items(self):
        return tuple(self._d.items())

    def items(self) -> 'CountsItemsView':
        return CountsItemsView(self)

    def __str__(self) -> str:
        return str(self._d)

    def __repr__(self) -> str:
        return type(self).__qualname__ + f'({repr(self._d)})'

    def reduce(self) -> 'Counts':
        """Divides all counts by their greatest common denominator."""
        gcd = math.gcd(*self.values())
        if gcd <= 1:
            return self
        data = [(outcome, weight // gcd) for outcome, weight in self.items()]
        return Counts(data)


class CountsKeysView(KeysView, Sequence):

    def __init__(self, counts: Counts):
        self._counts = counts

    def __getitem__(self, index):
        return self._counts._keys[index]

    def __len__(self):
        return len(self._counts)

    def __contains__(self, key) -> bool:
        return key in self._counts

    def __iter__(self) -> Iterator:
        return iter(self._counts._keys)

    def __eq__(self, other):
        return self._counts._keys == other


class CountsValuesView(ValuesView[int], Sequence[int]):

    def __init__(self, counts: Counts):
        self._counts = counts

    def __getitem__(self, index):
        return self._counts._values[index]

    def __len__(self) -> int:
        return len(self._counts)

    def __contains__(self, value) -> bool:
        return value in self._counts._values

    def __iter__(self) -> Iterator[int]:
        return iter(self._counts._values)

    def __eq__(self, other):
        return self._counts._values == other


class CountsItemsView(ItemsView[Any, int], Sequence[tuple[Any, int]]):

    def __init__(self, counts: Counts):
        self._counts = counts

    def __getitem__(self, index):
        return self._counts._items[index]

    def __len__(self) -> int:
        return len(self._counts)

    def __iter__(self) -> Iterator[tuple[Any, int]]:
        return iter(self._counts._items)

    def __eq__(self, other):
        return self._counts._items == other
