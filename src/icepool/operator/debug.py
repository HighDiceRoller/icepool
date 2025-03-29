__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator
from icepool.order import Order, UnsupportedOrder

from icepool.typing import T
from typing import Callable, Collection, Hashable, Iterable, Iterator, MutableSequence, Sequence


class MultisetForceOrder(MultisetOperator[T]):
    """Forces a particular evaluation order and does nothing else."""

    def __init__(self, child: MultisetExpression[T], *,
                 force_order: Order) -> None:
        self._children = (child, )
        self._force_order = force_order

    def _initial_state(
            self, order, outcomes, child_cardinalities: MutableSequence,
            source_cardinalities: Iterator,
            param_cardinalities: Sequence) -> tuple[None, int | None]:
        if self._force_order != Order.Any and order != self._force_order:
            raise UnsupportedOrder()
        return None, child_cardinalities[0]

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    param_counts):
        return None, child_counts[0]

    @property
    def _expression_key(self):
        return type(self), self._force_order
