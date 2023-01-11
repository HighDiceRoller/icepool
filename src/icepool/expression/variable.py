__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Outcome

from functools import cached_property
from typing import Final, Hashable, Literal, overload


class MultisetVariable(MultisetExpression):

    def __init__(self, index: int = 0):
        """
        Args:
            index: This corresponds to the index of the `*generators` passed
                to an evaluation. May be negative.
        """
        self._index = index

    def evaluate_counts(self, outcome: Outcome, *counts: int) -> int:
        return counts[self._index]

    @cached_property
    def _key_tuple(self) -> tuple[Hashable, ...]:
        return type(self), self._index


class MultisetVariableFactory():

    @overload
    def __getitem__(cls, index: int) -> 'MultisetVariable':
        """Generates a `MultisetVariable`."""

    @overload
    def __getitem__(cls, index: slice) -> 'tuple[MultisetVariable, ...]':
        """Generates a tuple of `MultisetVariable`s."""

    @overload
    def __getitem__(
        cls, index: int | slice
    ) -> 'MultisetVariable | tuple[MultisetVariable, ...]':
        """Generates a `MultisetVariable` or a tuple thereof."""

    def __getitem__(
        cls, index: int | slice
    ) -> 'MultisetVariable | tuple[MultisetVariable, ...]':
        """Generates a `MultisetVariable` or a tuple thereof."""
        if isinstance(index, int):
            return MultisetVariable(index)
        elif isinstance(index, slice):
            if index.stop is None:
                raise ValueError('A stop index must be provided.')
            if index.stop < 0 or (index.start is not None and index.start < 0):
                raise ValueError('Variable indexes cannot be negative.')

            return tuple(
                MultisetVariable(i)
                for i in range(index.start, index.stop, index.step))


multiset_variables: Final = MultisetVariableFactory()
"""Indexable object to get `MultisetVariable`s."""