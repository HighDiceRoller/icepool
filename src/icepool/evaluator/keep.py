__docformat__ = 'google'

from typing import Any
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.order import Order, UnsupportedOrder


class KeepEvaluator(MultisetEvaluator[Any, Any]):
    """Produces the outcome at a given sorted index.

    The attached generator or expression must produce enough values to reach
    the sorted index; otherwise, this raises `IndexError`.

    Negative incoming counts are treated as zero counts.
    """

    def initial_state(self, order, outcomes, *, index):
        if index is None:
            remaining = 1
        elif (order > 0) != (index >= 0):
            raise UnsupportedOrder()
        else:
            if index >= 0:
                remaining = index + 1
            else:
                remaining = -index
        return None, remaining

    def next_state(self, state, order, outcome, count):
        result, remaining = state

        remaining = max(remaining - max(count, 0), 0)
        if remaining == 0 and result is None:
            result = outcome
        return result, remaining

    def final_outcome(self, final_state, order, outcomes, /, *, index):
        if final_state is None:
            raise IndexError('No outcomes were seen.')
        result, remaining = final_state
        if result is None:
            raise IndexError(
                f'Evaluation ended {remaining} element(s) short of reaching the kept index.'
            )
        return result

    @property
    def dungeon_key(self):
        return (type(self), )


keep_evaluator = KeepEvaluator()
"""Shared instance for caching."""
