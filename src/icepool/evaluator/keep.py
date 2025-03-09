__docformat__ = 'google'

from typing import Any
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.order import Order, UnsupportedOrderError


class KeepEvaluator(MultisetEvaluator[Any, Any]):
    """Produces the outcome at a given sorted index.

    The attached generator or expression must produce enough values to reach
    the sorted index; otherwise, this raises `IndexError`.

    Negative incoming counts are treated as zero counts.
    """

    def next_state_ascending(self, state, outcome, count, /, *, index):
        """Implementation."""
        if state is None:
            result = None
            if index is None:
                remaining = 1
            elif index < 0:
                raise UnsupportedOrderError()
            else:
                remaining = index + 1
        else:
            result, remaining = state
        remaining = max(remaining - max(count, 0), 0)
        if remaining == 0 and result is None:
            result = outcome
        return result, remaining

    def next_state_descending(self, state, outcome, count, /, *, index):
        """Implementation."""
        if state is None:
            result = None
            if index is None:
                remaining = 1
            elif index > 0:
                raise UnsupportedOrderError()
            else:
                remaining = -index
        else:
            result, remaining = state
        remaining = max(remaining - max(count, 0), 0)
        if remaining == 0 and result is None:
            result = outcome
        return result, remaining

    def final_outcome(self, final_state, /, *, index):
        """Implementation."""
        if final_state is None:
            raise IndexError('No outcomes were seen.')
        result, remaining = final_state
        if result is None:
            raise IndexError(
                f'Evaluation ended {remaining} element(s) short of reaching the kept index.'
            )
        return result


keep_evaluator = KeepEvaluator()
"""Shared instance for caching."""
