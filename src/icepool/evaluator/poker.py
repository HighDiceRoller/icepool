"""Evaluators for poker/Yahtzee-like mechanics."""

__docformat__ = 'google'

import icepool
from icepool.evaluator.multiset_evaluator import MultisetEvaluator

from icepool.typing import Outcome, Order
from typing import Any, Collection, Literal, Sequence


class HighestOutcomeAndCountEvaluator(MultisetEvaluator[Any, tuple[Any, int]]):
    """The highest outcome that has positive count, along with that count.

    If no outcomes have positive count, an arbitrary outcome will be produced
    with a 0 count.
    """

    def next_state(self, state, outcome, count):
        """Implementation."""
        count = max(count, 0)
        if state is None:
            return outcome, count
        elif count > 0:
            if state[1] > 0:
                return max(state, (outcome, count))
            else:
                return outcome, count
        else:
            return state

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any


class AllCountsEvaluator(MultisetEvaluator[Any, tuple[int, ...]]):
    """All counts in ascending order.

    In other words, this produces tuples of the sizes of all matching sets.
    """

    def __init__(self, *, filter: int | None = 1) -> None:
        """
        Args:
            filter: Any counts below this value will not be in the output.
                For example, `filter=2` will only produce pairs and better.
                If `None`, no filtering will be done.
        """
        self._filter = filter

    def next_state(self, state, outcome, count):
        """Implementation."""
        state = state or ()
        if self._filter is None or count >= self._filter:
            state = state + (count,)
            return tuple(sorted(state))
        else:
            return state

    def final_outcome(self, final_state) -> tuple:
        """Implementation."""
        if final_state is None:
            return ()
        else:
            return final_state

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any

    def alignment(self, outcomes: Sequence) -> Collection:
        """Always sees zeros."""
        return outcomes


class LargestCountEvaluator(MultisetEvaluator[Any, int]):
    """The largest count of any outcome."""

    def next_state(self, state, _, count):
        """Implementation."""
        return max(state or count, count)

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any


class LargestCountAndOutcomeEvaluator(MultisetEvaluator[Any, tuple[int, Any]]):
    """The largest count of any outcome, along with that outcome."""

    def next_state(self, state, outcome, count):
        """Implementation."""
        return max(state or (count, outcome), (count, outcome))

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any


class LargestStraightEvaluator(MultisetEvaluator[int, int]):
    """The size of the largest straight."""

    def next_state(self, state, _, count):
        """Implementation."""
        best_run, run = state or (0, 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max(best_run, run), run

    def final_outcome(self, final_state) -> int:
        """Implementation."""
        if final_state is None:
            return 0
        return final_state[0]

    def order(self) -> Literal[Order.Ascending]:
        """Ascending order."""
        return Order.Ascending

    alignment = MultisetEvaluator.range_alignment


class LargestStraightAndOutcomeEvaluator(MultisetEvaluator[int, tuple[int,
                                                                      int]]):
    """The size of the largest straight, along with the greatest outcome in that straight."""

    def next_state(self, state, outcome, count):
        """Implementation."""
        best_run_and_outcome, run = state or ((0, outcome), 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max(best_run_and_outcome, (run, outcome)), run

    def final_outcome(self, final_state) -> tuple[int, int]:
        """Implementation."""
        return final_state[0]

    def order(self) -> Literal[Order.Ascending]:
        """Ascending order."""
        return Order.Ascending

    alignment = MultisetEvaluator.range_alignment
