"""Evaluators for poker/Yahtzee-like mechanics."""

__docformat__ = 'google'

from icepool.evaluator.multiset_evaluator import MultisetEvaluator

import operator

from typing import Any, Callable, Collection, Final, Literal, Sequence


def make_select_function(
        which: Callable[[Any], bool] | Collection | None
) -> Callable[[Any], bool]:
    if which is None:
        return lambda outcome: False
    elif callable(which):
        return which
    else:
        which = frozenset(which)
        return lambda outcome: outcome in which


class HighestOutcomeAndCountEvaluator(MultisetEvaluator[Any, tuple[Any, int]]):
    """The highest outcome that has positive count, along with that count.

    If no outcomes have positive count, the result is the min outcome with a count of 0.
    """

    def next_state(self, state, order, outcome, count):
        """Implementation."""
        count = max(count, 0)

        if state is None:
            return outcome, count

        if count > 0 and outcome > state[0]:
            return outcome, count

        if count == 0 and state[1] == 0:
            return min(outcome, state[0]), 0

        return state

    def extra_outcomes(self, outcomes: Sequence) -> Collection:
        """Always sees zero counts."""
        return outcomes

    @property
    def next_state_key(self):
        return type(self)


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

    def next_state(self, state, order, outcome, count):
        """Implementation."""
        state = state or ()
        if self._filter == 'all' or count >= self._filter:
            state = state + (count, )
            return tuple(sorted(state, reverse=True))
        else:
            return state

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, size) -> tuple:
        """Implementation."""
        if final_state is None:
            return ()
        else:
            return final_state

    def extra_outcomes(self, outcomes: Sequence) -> Collection:
        """Always sees zero counts."""
        return outcomes

    @property
    def next_state_key(self):
        return (type(self), self._filter)


class LargestCountEvaluator(MultisetEvaluator[Any, int]):
    """The largest count of any outcome."""

    def next_state(self, state, order, outcome, count):
        """Implementation."""
        return max(state or count, count)

    @property
    def next_state_key(self):
        return type(self)


largest_count_evaluator: Final = LargestCountEvaluator()
"""Shared instance for caching."""


class LargestCountWithWildEvaluator(MultisetEvaluator[Any, int]):

    def __init__(self, wild: Callable[[Any], bool] | Collection | None,
                 wild_low: Callable[[Any], bool] | Collection | None,
                 wild_high: Callable[[Any], bool] | Collection | None):
        self._wild = make_select_function(wild)
        self._wild_low = make_select_function(wild_low)
        self._wild_high = make_select_function(wild_high)

    def next_state(self, state, order, outcome, count):
        is_wild = self._wild(outcome)
        if order > 0:
            is_wild_early = is_wild or self._wild_low(outcome)
            is_wild_late = is_wild or self._wild_high(outcome)
        else:
            is_wild_early = is_wild or self._wild_high(outcome)
            is_wild_late = is_wild or self._wild_low(outcome)
        if state is None:
            if is_wild_early:
                return count, count
            else:
                return count, 0
        best, total_wild_early = state
        if is_wild_late:
            best += count
        best = max(best, count + total_wild_early)
        if is_wild_early:
            total_wild_early += count
        return best, total_wild_early

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, size) -> int:
        return final_state[0]


class LargestCountAndOutcomeEvaluator(MultisetEvaluator[Any, tuple[int, Any]]):
    """The largest count of any outcome, along with that outcome."""

    def next_state(self, state, order, outcome, count):
        """Implementation."""
        return max(state or (count, outcome), (count, outcome))

    @property
    def next_state_key(self):
        return type(self)


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

    def next_state(self, state, order, outcome, left, right):
        if right == 0:
            return state
        current = left // right
        if state is None:
            return current
        else:
            return min(state, current)

    def final_outcome(self, final_state, order, outcomes, left_size,
                      right_size):
        if final_state is None:
            if self._empty_divisor is None:
                raise ZeroDivisionError(
                    'Empty divisor. Set empty_divisor_outcome if you want a particular value in this case.'
                )
            else:
                return self._empty_divisor
        return final_state

    @property
    def next_state_key(self):
        return (type(self), )


class LargestStraightEvaluator(MultisetEvaluator[int, int]):
    """The size of the largest straight."""

    def next_state(self, state, order, outcome, count):
        best_run, run = state or (0, 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max(best_run, run), run

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, size) -> int:
        if final_state is None:
            return 0
        return final_state[0]

    extra_outcomes = MultisetEvaluator.consecutive

    @property
    def next_state_key(self):
        return type(self)


largest_straight_evaluator: Final = LargestStraightEvaluator()
"""Shared instance for caching."""


class LargestStraightAndOutcomeEvaluator(MultisetEvaluator[int, tuple[int,
                                                                      int]]):
    """The size of the largest straight among the elements and the highest (optionally, lowest) outcome in that straight.

    Straight size is prioritized first, then the outcome.

    Outcomes must be `int`s.
    """

    def __init__(self, priority: Literal['low', 'high']):
        """Constructor.
        Args:
            priority: Controls which outcome within the straight is returned,
                and which straight is picked if there is a tie for largest
                straight.
        """
        if priority == 'low':
            self._prioritize_highest = False
        elif priority == 'high':
            self._prioritize_highest = True
        else:
            raise ValueError("priority must be 'low' or 'high'.")

    def initial_state(self, order, outcomes, size):
        if order > 0:
            return 0, outcomes[-1], 0
        else:
            return 0, outcomes[0], 0

    def next_state(self, state, order, outcome, count):
        best_run, best_outcome, run = state
        if count >= 1:
            run += 1
        else:
            run = 0
        if self._prioritize_highest == (order > 0):
            if run >= best_run:
                return run, outcome, run
            else:
                return best_run, best_outcome, run
        else:
            if run > best_run:
                return run, outcome - (run - 1) * order.value, run
            else:
                return best_run, best_outcome, run

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, size) -> tuple[int, int]:
        best_run, best_outcome, run = final_state
        return best_run, best_outcome

    extra_outcomes = MultisetEvaluator.consecutive

    @property
    def next_state_key(self):
        return (type(self), self._prioritize_highest)


largest_straight_and_outcome_evaluator_low: Final = LargestStraightAndOutcomeEvaluator(
    'low')
"""Shared instance for caching."""
largest_straight_and_outcome_evaluator_high: Final = LargestStraightAndOutcomeEvaluator(
    'high')
"""Shared instance for caching."""


class AllStraightsEvaluator(MultisetEvaluator[int, tuple[int, ...]]):
    """The sizes of all straights in descending order.

    Each element can only contribute to one straight, though duplicate
    elements can produces straights that overlap in outcomes. In this case,
    elements are preferentially assigned to the longer straight.
    """

    def next_state(self, state, order, outcome, count):
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

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, size) -> tuple[int, ...]:
        """Implementation."""
        current_runs, ended_runs = final_state or ((), ())
        return tuple(sorted(current_runs + ended_runs, reverse=True))

    extra_outcomes = MultisetEvaluator.consecutive

    @property
    def next_state_key(self):
        return type(self)


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

    def next_state(self, state, order, outcome, count):
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

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes,
            size) -> tuple[tuple[int, int], ...]:
        """Implementation."""
        current_run_length, current_run_score, ended_runs = final_state or (
            None, None, ())
        if current_run_length is not None:
            current_run = (current_run_length, current_run_score)
            ended_runs = tuple(
                sorted(ended_runs + (current_run, ), reverse=True))
        return ended_runs

    extra_outcomes = MultisetEvaluator.consecutive
