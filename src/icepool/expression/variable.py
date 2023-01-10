__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Outcome

from functools import cached_property
from typing import Hashable, Literal, overload


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

    @overload
    def __class_getitem__(cls, index: int) -> 'MultisetVariable':
        """Generates a `MultisetVariable`."""

    @overload
    def __class_getitem__(cls, index: slice) -> 'tuple[MultisetVariable, ...]':
        """Generates a tuple of `MultisetVariable`s."""

    @overload
    def __class_getitem__(
        cls, index: int | slice
    ) -> 'MultisetVariable | tuple[MultisetVariable, ...]':
        """Generates a `MultisetVariable` or a tuple thereof."""

    def __class_getitem__(
        cls, index: int | slice
    ) -> 'MultisetVariable | tuple[MultisetVariable, ...]':
        """Generates a `MultisetVariable` or a tuple thereof."""
        if isinstance(index, int):
            return MultisetVariable(index)
        elif isinstance(index, slice):
            if index.start is not None:
                if index.stop is not None:
                    # both start and stop
                    if (index.start < 0) != (index.stop < 0):
                        raise ValueError(
                            'If both provided, start and stop of the slice must both be positive or non-positive.'
                        )
                else:
                    # start only
                    if index.start >= 0:
                        raise ValueError(
                            'If stop of the slice is not provided, start must be positive.'
                        )
            else:
                if index.stop is not None:
                    # stop only
                    if index.stop < 0:
                        raise ValueError(
                            'If start of the slice is not provided, stop must be non-positive.'
                        )
                else:
                    # neither start nor stop
                    raise ValueError(
                        'At least one of start or stop of the slice must be provided.'
                    )

            return tuple(
                MultisetVariable(i)
                for i in range(index.start, index.stop, index.step))
