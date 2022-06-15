__docformat__ = 'google'

import icepool

from functools import cached_property
import math

from collections.abc import ItemsView, Iterator, KeysView, Mapping, MutableMapping, Sequence, ValuesView
from typing import Any


class Counts(Mapping[Any, int]):
    """Immutable dictionary whose values are integers.

    The values of keys(), values(), and items() are also Sequences, which means
    they can be indexed.
    """

    _mapping: Mapping[Any, int]

    def __init__(self, items: Sequence[tuple[Any, int]]):
        """
        Args:
            items: A sequence of key, value pairs.
        """
        mapping: MutableMapping[Any, int] = {}
        for key, value in items:
            if key is None:
                raise TypeError('None is not a valid key.')
            if isinstance(key, icepool.SpecialValue):
                raise TypeError(str(key) + ' is not a valid key.')
            if not isinstance(value, int):
                raise ValueError('Values must be ints, got ' +
                                 type(value).__name__)
            if key not in mapping:
                mapping[key] = value
            else:
                mapping[key] += value
        self._mapping = mapping

    @cached_property
    def _has_zero_values(self):
        return 0 in self.values()

    def has_zero_values(self) -> bool:
        """Returns `True` iff `self` contains at least one zero weight. """
        return self._has_zero_values

    def __len__(self) -> int:
        return len(self._mapping)

    def __contains__(self, key) -> bool:
        return key in self._mapping

    def __getitem__(self, key) -> int:
        return self._mapping[key]

    def __iter__(self) -> Iterator:
        return iter(self._mapping)

    @cached_property
    def _keys(self):
        return tuple(self._mapping.keys())

    def keys(self) -> 'CountsKeysView':
        return CountsKeysView(self)

    @cached_property
    def _values(self):
        return tuple(self._mapping.values())

    def values(self) -> 'CountsValuesView':
        return CountsValuesView(self)

    @cached_property
    def _items(self):
        return tuple(self._mapping.items())

    def items(self) -> 'CountsItemsView':
        return CountsItemsView(self)

    def __str__(self) -> str:
        return str(self._mapping)

    def __repr__(self) -> str:
        return type(self).__qualname__ + f'({repr(self._mapping)})'

    def reduce(self) -> 'Counts':
        """Divides all counts by their greatest common denominator."""
        gcd = math.gcd(*self.values())
        if gcd <= 1:
            return self
        data = [(outcome, weight // gcd) for outcome, weight in self.items()]
        return Counts(data)


class CountsKeysView(KeysView, Sequence):
    """This functions as both a `KeysView` and a `Sequence`."""

    def __init__(self, counts: Counts):
        self._mapping = counts

    def __getitem__(self, index):
        return self._mapping._keys[index]

    def __len__(self):
        return len(self._mapping)

    def __eq__(self, other):
        return self._mapping._keys == other


class CountsValuesView(ValuesView[int], Sequence[int]):
    """This functions as both a `ValuesView` and a `Sequence`."""

    def __init__(self, counts: Counts):
        self._mapping = counts

    def __getitem__(self, index):
        return self._mapping._values[index]

    def __len__(self) -> int:
        return len(self._mapping)

    def __eq__(self, other):
        return self._mapping._values == other


class CountsItemsView(ItemsView[Any, int], Sequence[tuple[Any, int]]):
    """This functions as both an `ItemsView` and a `Sequence`."""

    def __init__(self, counts: Counts):
        self._mapping = counts

    def __getitem__(self, index):
        return self._mapping._items[index]

    def __eq__(self, other):
        return self._mapping._items == other
