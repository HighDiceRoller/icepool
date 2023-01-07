"""Evaluators for poker/Yahtzee-like mechanics."""

__docformat__ = 'google'

import icepool
from icepool.constant import Order
from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator

from typing import Any


class AllMatchingSetsEvaluator(OutcomeCountEvaluator[Any, tuple[int, ...],
                                                     int]):
    """All counts in ascending order."""

    def __init__(self, *, positive_only: bool = True):
        """
        Args:
            positive_only: If `True` (default), any zero and negative values
                in the result are removed.
        """
        self._positive_only = positive_only

    def next_state(self, state, outcome, count):
        """Implementation."""
        state = (state or ()) + (count,)
        return tuple(sorted(state))

    def final_outcome(self, final_state, *_):
        """Implementation."""
        if final_state is None:
            return ()
        if self._positive_only:
            return tuple(x for x in final_state if x > 0)
        else:
            return final_state

    def order(self, *_):
        """Allows any order."""
        return Order.Any


class LargestMatchingSetEvaluator(OutcomeCountEvaluator[Any, int, int]):
    """The largest matching set of a generator."""

    def next_state(self, state, _, count):
        """Implementation."""
        return max(state or count, count)

    def order(self, *_):
        """Allows any order."""
        return Order.Any


class LargestMatchingSetAndOutcomeEvaluator(OutcomeCountEvaluator[Any,
                                                                  tuple[int,
                                                                        Any],
                                                                  int]):

    def next_state(self, state, outcome, count):
        """Implementation."""
        return max(state or (count, outcome), (count, outcome))

    def order(self, *_):
        """Allows any order."""
        return Order.Any


class LargestStraightEvaluator(OutcomeCountEvaluator[int, int, int]):

    def next_state(self, state, _, count):
        """Implementation."""
        best_run, run = state or (0, 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max(best_run, run), run

    def final_outcome(self, final_state, *_):
        """Implementation."""
        if final_state is None:
            return 0
        return final_state[0]

    def order(self, *_):
        """Ascending order."""
        return Order.Ascending

    alignment = OutcomeCountEvaluator.range_alignment


class LargestStraightAndOutcomeEvaluator(OutcomeCountEvaluator[int, tuple[int,
                                                                          int],
                                                               int]):

    def next_state(self, state, outcome, count):
        """Implementation."""
        best_run_and_outcome, run = state or ((0, outcome), 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max(best_run_and_outcome, (run, outcome)), run

    def final_outcome(self, final_state, *_):
        """Implementation."""
        return final_state[0]

    def order(self, *_):
        """Ascending order."""
        return Order.Ascending

    alignment = OutcomeCountEvaluator.range_alignment
