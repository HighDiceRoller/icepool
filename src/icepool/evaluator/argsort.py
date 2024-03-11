__docformat__ = 'google'

from icepool.evaluator.multiset_evaluator import MultisetEvaluator

from icepool.typing import Order
from typing import Any


class ArgsortEvaluator(MultisetEvaluator[Any, tuple[tuple[int, ...], ...]]):
    """Returns the indexes of the originating multisets for each rank in their additive union."""

    def __init__(self,
                 *,
                 order: Order = Order.Descending,
                 limit: int | None = None):
        self._order = order
        self._limit = limit

    def next_state(self, state, _, *counts):
        """Implementation."""
        if state is None:
            state = ()
        if (self._limit is None or len(state) < self._limit) and any(
                count > 0 for count in counts):
            to_append = sum(((i, ) * count for i, count in enumerate(counts)),
                            start=())
            state += (to_append, )
        return state

    def final_outcome(self, final_state):
        return final_state or ()

    def order(self) -> Order:
        return self._order
