__docformat__ = 'google'

from typing import Any
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import Outcome, Order


class KeepEvaluator(MultisetEvaluator[Any, Any]):
    """Produces the outcome at a given sorted index.

    The attached generator or expression must produce enough values to reach
    the sorted index; otherwise, this raises `IndexError`.
    """

    def __init__(self, index: int | None = None) -> None:
        """Constructor.

        Args:
            index: The index to keep.
                * If non-negative, this runs in ascending order.
                * If negative, this runs in descending order.
                * If `None`, this assumes only one element is produced.
        """
        if index is None:
            self._skip = 1
            self._order = Order.Any
        elif index >= 0:
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
        if count > 0 and self._order == Order.Any and result is not None:
            raise IndexError('Expected exactly one element.')
        remaining -= count
        if remaining <= 0 and result is None:
            result = outcome
        return result, remaining

    def final_outcome(self, final_state):
        """Implementation."""
        if final_state is None:
            raise IndexError('No outcomes were seen.')
        if final_state[0] is None:
            if self._order == Order.Any:
                raise IndexError('Expected exactly one element.')
            else:
                raise IndexError(
                    f'Evaluation ended {final_state[1]} element(s) short of reaching the kept index.'
                )
        return final_state[0]

    def order(self) -> Order:
        """The required order is determined by whether the index is negative."""
        return self._order
