__docformat__ = 'google'

from typing import Any
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import Outcome, Order


class KeepEvaluator(MultisetEvaluator[Any, Any]):
    """Produces the outcome at a given sorted index.

    The attached generator or expression must produce enough values to reach
    the sorted index; otherwise, this raises `IndexError`.
    """

    def __init__(self, index: int) -> None:
        if index >= 0:
            self._skip = index + 1
            self._order = Order.Ascending
        else:
            self._skip = -index
            self._order = Order.Descending

    def next_state(self, state, outcome, count):
        """Implementation."""
        if count < 0:
            raise IndexError(
                'KeepEvaluator is not compatible with incoming negative counts.'
            )
        result, remaining = state or (None, self._skip)
        remaining -= count
        if remaining <= 0 and result is None:
            result = outcome
        return result, remaining

    def final_outcome(self, final_state):
        """Implementation."""
        if final_state is None:
            raise IndexError('No outcomes were seen.')
        if final_state[0] is None:
            raise IndexError(
                f'Evaluation ended {final_state[1]} elements short of reaching the kept index.'
            )
        return final_state[0]

    def order(self) -> Order:
        """The required order is determined by whether the index is negative."""
        return self._order
