__docformat__ = 'google'

import icepool
from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Order, Outcome

from functools import cached_property
from typing import Any, Final, Hashable, Literal, Sequence, overload


class MultisetVariable(MultisetExpression[Any]):
    """Represents an input multiset.

    All expressions start from these.
    """

    def __init__(self, index: int = 0) -> None:
        """
        Args:
            index: This corresponds to the index of the `*counts` passed
                to an evaluation. Must be non-negative.
        """
        self._index = index

    def _next_state(self, state, outcome: Outcome, bound_counts: tuple[int,
                                                                       ...],
                    counts: tuple[int, ...]) -> tuple[Hashable, int]:
        # We don't need any state, so always return str(self) as the state as
        # a diagnostic marker.
        return str(self), counts[self._index]

    def _order(self):
        return Order.Any

    def _arity(self) -> int:
        return self._index + 1

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return ()

    def __str__(self) -> str:
        return f'mv[{self._index}]'
