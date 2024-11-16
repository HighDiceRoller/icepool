"""Evaluators for poker/Yahtzee-like mechanics."""

__docformat__ = 'google'

import icepool
from icepool.evaluator.multiset_evaluator import MultisetEvaluator

import operator

from icepool.typing import Order
from typing import Any, Callable, Collection, Final, Literal, Sequence


class HighestOutcomeAndCountEvaluator(MultisetEvaluator[Any, tuple[Any, int]]):
    """The highest outcome that has positive count, along with that count.

    If no outcomes have positive count, the result is the min outcome with a count of 0.
    """

    def next_state(self, state, outcome, count):
        """Implementation."""
        count = max(count, 0)

        if state is None:
            return outcome, count

        if count > 0 and outcome > state[0]:
            return outcome, count

        if count == 0 and state[1] == 0:
            return min(outcome, state[0]), 0

        return state

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any

    def extra_outcomes(self, outcomes: Sequence) -> Collection:
        """Always sees zero counts."""
        return outcomes


highest_outcome_and_count_evaluator: Final = HighestOutcomeAndCountEvaluator()
"""Shared instance for caching."""


class AllCountsEvaluator(MultisetEvaluator[Any, tuple[int, ...]]):
    """All counts in descending order.

    In other words, this produces tuples of the sizes of all matching sets.
    """

    def __init__(self, *, filter: int | Literal['all'] = 1) -> None:
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
        if self._filter == 'all' or count >= self._filter:
            state = state + (count, )
            return tuple(sorted(state, reverse=True))
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

    def extra_outcomes(self, outcomes: Sequence) -> Collection:
        """Always sees zero counts."""
        return outcomes


class LargestCountEvaluator(MultisetEvaluator[Any, int]):
    """The largest count of any outcome."""

    def next_state(self, state, _, count):
        """Implementation."""
        return max(state or count, count)

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any


largest_count_evaluator: Final = LargestCountEvaluator()
"""Shared instance for caching."""


class LargestCountAndOutcomeEvaluator(MultisetEvaluator[Any, tuple[int, Any]]):
    """The largest count of any outcome, along with that outcome."""

    def next_state(self, state, outcome, count):
        """Implementation."""
        return max(state or (count, outcome), (count, outcome))

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any


largest_count_and_outcome_evaluator: Final = LargestCountAndOutcomeEvaluator()
"""Shared instance for caching."""


class CountSubsetEvaluator(MultisetEvaluator[Any, int]):
    """The number of times the right side is contained in the left side."""

    def __init__(self, *, empty_divisor: int | None = None):
        """
        Args:
            empty_divisor: If the divisor is empty, the outcome will be this.
                If not set, `ZeroDivisionError` will be raised for an empty
                right side.
        """
        self._empty_divisor = empty_divisor

    def next_state(self, state, _, left, right):
        if right == 0:
            return state
        current = left // right
        if state is None:
            return current
        else:
            return min(state, current)

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any

    def final_outcome(self, final_state):
        if final_state is None:
            if self._empty_divisor is None:
                raise ZeroDivisionError(
                    'Empty divisor. Set empty_divisor_outcome if you want a particular value in this case.'
                )
            else:
                return self._empty_divisor
        return final_state


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

    extra_outcomes = MultisetEvaluator.consecutive


largest_straight_evaluator: Final = LargestStraightEvaluator()
"""Shared instance for caching."""


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

    extra_outcomes = MultisetEvaluator.consecutive


largest_straight_and_outcome_evaluator: Final = LargestStraightAndOutcomeEvaluator(
)
"""Shared instance for caching."""


class AllStraightsEvaluator(MultisetEvaluator[int, tuple[int, ...]]):
    """The sizes of all straights in descending order.

    Each element can only contribute to one straight, though duplicate
    elements can produces straights that overlap in outcomes. In this case,
    elements are preferentially assigned to the longer straight.
    """

    def next_state(self, state, _, count):
        """Implementation."""
        current_runs, ended_runs = state or ((), ())
        if count < len(current_runs):
            next_current_runs = tuple(x + 1 for x in current_runs[:count])
            next_ended_runs = tuple(
                sorted(ended_runs + current_runs[count:], reverse=True))
        else:
            next_current_runs = tuple(
                x + 1
                for x in current_runs) + (1, ) * (count - len(current_runs))
            next_ended_runs = ended_runs
        return next_current_runs, next_ended_runs

    def final_outcome(self, final_state) -> tuple[int, ...]:
        """Implementation."""
        current_runs, ended_runs = final_state or ((), ())
        return tuple(sorted(current_runs + ended_runs, reverse=True))

    def order(self) -> Literal[Order.Ascending]:
        """Ascending order."""
        return Order.Ascending

    extra_outcomes = MultisetEvaluator.consecutive


all_straights_evaluator: Final = AllStraightsEvaluator()
"""Shared instance for caching."""


class AllStraightsReduceCountsEvaluator(MultisetEvaluator[int,
                                                          tuple[tuple[int,
                                                                      int],
                                                                ...]]):
    """All straights with a reduce operation on the counts.

    This can be used to evaluate e.g. cribbage-style straight counting.

    The result is a tuple of `(run_length, run_score)`s."""

    def __init__(self, reducer: Callable[[int, int], int] = operator.mul):
        """Constructor.

        Args:
            reducer: How to reduce the counts within each straight. The default
                is `operator.mul`, which counts the number of ways to pick
                elements for each straight, e.g. cribbage.
        """
        self._reducer = reducer

    def next_state(self, state, _, count):
        """Implementation."""
        current_run_length, current_run_score, ended_runs = state or (None,
                                                                      None, ())
        if count > 0:
            if current_run_length is None:
                current_run_length = 1
                current_run_score = count
            else:
                current_run_length += 1
                current_run_score = self._reducer(current_run_score, count)
        else:
            if current_run_length is not None:
                current_run = (current_run_length, current_run_score)
                ended_runs = tuple(
                    sorted(ended_runs + (current_run, ), reverse=True))
            current_run_length = None
            current_run_score = None
        return current_run_length, current_run_score, ended_runs

    def final_outcome(self, final_state) -> tuple[tuple[int, int], ...]:
        """Implementation."""
        current_run_length, current_run_score, ended_runs = final_state or (
            None, None, ())
        if current_run_length is not None:
            current_run = (current_run_length, current_run_score)
            ended_runs = tuple(
                sorted(ended_runs + (current_run, ), reverse=True))
        return ended_runs

    extra_outcomes = MultisetEvaluator.consecutive
