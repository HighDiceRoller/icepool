__docformat__ = 'google'

import icepool

from functools import cached_property
import math

from icepool.typing import T
from typing import Collection, ItemsView, Iterable, Iterator, KeysView, Mapping, MutableMapping, Sequence, ValuesView


class Counts(Mapping[T, int]):
    """Immutable dictionary with sorted keys and `int` values.

    The values of keys(), values(), and items() are also Sequences, which means
    they can be indexed.
    """

    _mapping: Mapping[T, int]

    def __init__(self, items: Iterable[tuple[T, int]]):
        """
        Args:
            items: A Collection of key, value pairs.
                These will be sorted by key.
            sort_key: If provided, keys will be sorted using the result of this
                function.
        """

        try:
            items = sorted(items)
            if len(items) == 1:
                first_key = items[0][0]
                bool(first_key < first_key)
        except TypeError:
            raise TypeError(
                'Items do not appear to be sortable. '
                'Tip: Sequences containing dice or decks are not sortable. '
                'Use tupleize() or vectorize() to transform '
                'a sequence of dice into a die with sequence outcomes '
                'according to the Cartesian product.')

        mapping: MutableMapping[T, int] = {}
        for key, value in items:
            if key is None:
                raise TypeError('None is not a valid key.')
            if key is icepool.Reroll:
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
    def _has_zero_values(self) -> bool:
        return 0 in self.values()

    def has_zero_values(self) -> bool:
        """`True` iff `self` contains at least one zero value. """
        return self._has_zero_values

    def __len__(self) -> int:
        return len(self._mapping)

    def __contains__(self, key) -> bool:
        return key in self._mapping

    def __getitem__(self, key) -> int:
        return self._mapping[key]

    def __iter__(self) -> Iterator[T]:
        return iter(self._mapping)

    @cached_property
    def _keys(self) -> Sequence[T]:
        return tuple(self._mapping.keys())

    def keys(self) -> 'CountsKeysView':
        return CountsKeysView(self)

    @cached_property
    def _values(self) -> Sequence[int]:
        return tuple(self._mapping.values())

    def values(self) -> 'CountsValuesView':
        return CountsValuesView(self)

    @cached_property
    def _items(self) -> Sequence[tuple[T, int]]:
        return tuple(self._mapping.items())

    def items(self) -> 'CountsItemsView[T]':
        return CountsItemsView(self)

    def __str__(self) -> str:
        return str(self._mapping)

    def __repr__(self) -> str:
        return type(self).__qualname__ + f'({repr(self._mapping)})'

    def __eq__(self, other) -> bool:
        if isinstance(other, Counts):
            return self._items == other._items
        else:
            return super().__eq__(other)

    @cached_property
    def _hash(self) -> int:
        return hash(self._items)

    def __hash__(self) -> int:
        return self._hash

    @cached_property
    def _remove_min(self) -> 'Counts[T]':
        return Counts(self.items()[1:])

    def remove_min(self) -> 'Counts[T]':
        """A `Counts` with the min element removed."""
        return self._remove_min

    @cached_property
    def _remove_max(self) -> 'Counts[T]':
        return Counts(self.items()[:-1])

    def remove_max(self) -> 'Counts[T]':
        """A `Counts` with the max element removed."""
        return self._remove_max

    def simplify(self) -> 'Counts[T]':
        """Divides all counts by their greatest common denominator."""
        gcd = math.gcd(*self.values())
        if gcd <= 1:
            return self
        data = [(outcome, value // gcd) for outcome, value in self.items()]
        return Counts(data)


class CountsKeysView(KeysView[T], Sequence[T]):
    """This functions as both a `KeysView` and a `Sequence`."""

    def __init__(self, counts: Counts[T]):
        self._mapping = counts

    def __getitem__(self, index):
        return self._mapping._keys[index]

    def __len__(self) -> int:
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


class CountsItemsView(ItemsView[T, int], Sequence[tuple[T, int]]):
    """This functions as both an `ItemsView` and a `Sequence`."""

    def __init__(self, counts: Counts):
        self._mapping = counts

    def __getitem__(self, index):
        return self._mapping._items[index]

    def __eq__(self, other):
        return self._mapping._items == other


def sorted_union(*args: Collection[T]) -> Sequence[T]:
    """Merge sets into a sorted sequence."""
    if not args:
        return ()
    return tuple(sorted(set.union(*(set(arg) for arg in args))))
