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

    _inners = ()

    def __init__(self, /, *, index: int = 0) -> None:
        """
        Args:
            index: This corresponds to the index of the `*counts` passed
                to an evaluation. Must be non-negative.
        """
        self._index = index

    def _make_unbound(self, *unbound_inners) -> 'icepool.MultisetExpression':
        return self

    def _next_state(self, state, outcome: Outcome, *counts:
                    int) -> tuple[Hashable, int]:
        # We don't need any state.
        return None, counts[self._index]

    def order(self):
        return Order.Any

    def _free_arity(self) -> int:
        return self._index + 1

    def __str__(self) -> str:
        return f'mv[{self._index}]'
