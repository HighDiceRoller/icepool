"""Concrete subclasses of OutcomeCountEvaluator."""

__docformat__ = 'google'

import icepool
from icepool.outcome_count_evaluator import Order, OutcomeCountEvaluator

from collections import defaultdict
from typing import Any, Callable, Collection, Container, Hashable, Mapping


class WrapFuncEvaluator(OutcomeCountEvaluator):
    """An `OutcomeCountEvaluator` created from a single provided function.

    `next_state()` simply calls that function.
    """

    def __init__(self, func: Callable, /):
        """Constructs a new instance given the function that should be called for `next_state()`.
        Args:
            func(state, outcome, *counts): This should take the same arguments
                as `next_state()`, minus `self`, and return the next state.
        """
        self._func = func

    def next_state(self, state: Hashable, outcome, *counts: int) -> Hashable:
        return self._func(state, outcome, *counts)


class JointEvaluator(OutcomeCountEvaluator):
    """EXPERIMENTAL: An `OutcomeCountEvaluator` that jointly evaluates sub-evaluators on the same roll(s) of a generator.

    It may be more efficient to write the joint evaluation directly; this is
    provided as a convenience.
    """

    def __init__(self, *sub_evaluators: OutcomeCountEvaluator):
        self._sub_evaluators = sub_evaluators

    def next_state(self, state, outcome, *counts: int) -> tuple[Hashable, ...]:
        """Runs `next_state` for all subevals.

        The state is a tuple of the substates.
        """
        if state is None:
            return tuple(
                evaluator.next_state(None, outcome, *counts)
                for evaluator in self._sub_evaluators)
        else:
            return tuple(
                evaluator.next_state(substate, outcome, *counts)
                for evaluator, substate in zip(self._sub_evaluators, state))

    def final_outcome(self, final_state,
                      *generators: icepool.OutcomeCountGenerator):
        """Runs `final_state` for all subevals.

        The final outcome is a tuple of the final suboutcomes.
        """
        return tuple(
            evaluator.final_outcome(final_substate, *generators) for evaluator,
            final_substate in zip(self._sub_evaluators, final_state))

    def order(self, *generators: icepool.OutcomeCountGenerator) -> int:
        """Determines the common order of the subevals.

        Raises:
            ValueError: If subevals have conflicting orders, i.e. some are
                ascending and others are descending.
        """
        suborders = tuple(
            evaluator.order(*generators) for evaluator in self._sub_evaluators)
        ascending = any(x > 0 for x in suborders)
        descending = any(x < 0 for x in suborders)
        if ascending and descending:
            raise ValueError('Sub-evals have conflicting orders.')
        elif ascending:
            return 1
        elif descending:
            return -1
        else:
            return 0


class SumEvaluator(OutcomeCountEvaluator):
    """Sums all outcomes."""

    def next_state(self, state, outcome, count):
        """Add the outcomes to the running total. """
        if state is None:
            return outcome * count
        else:
            return state + outcome * count

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return 0
        else:
            return final_state

    def order(self, *_):
        return Order.Any


sum_evaluator = SumEvaluator()


class ExpandEvaluator(OutcomeCountEvaluator):
    """Expands all results of a generator.

    This is expensive and not recommended unless there are few possibilities.
    """

    def next_state(self, state, outcome, count):
        if count < 0:
            raise ValueError(
                'EnumerateGenerator is not compatible with negative counts.')
        if state is None:
            return (outcome,) * count
        else:
            return state + (outcome,) * count

    def order(self, *_):
        return Order.Any


expand_evaluator = ExpandEvaluator()


class CountInEvaluator(OutcomeCountEvaluator):
    """Counts how many of the given outcome are produced by the generator."""

    def __init__(self, target: Container, /):
        self._target = target

    def next_state(self, state, outcome, count):
        if outcome in self._target:
            state = (state or 0) + count
        return state

    def final_outcome(self, final_state, *_):
        return final_state or 0

    def order(self, *_):
        return Order.Any


class SubsetTargetEvaluator(OutcomeCountEvaluator):
    """Base class for evaluators that look for a subset (possibly with repeated elements)."""

    def __init__(self, target: Collection | Mapping[Any, int], /):
        """
        Args:
            target: Either a collection of outcomes, possibly with repeated elements.
                Or a mapping from outcomes to counts.
        """
        if isinstance(target, Mapping):
            self._target = target
        else:
            self._target = defaultdict(int)
            for outcome in target:
                self._target[outcome] += 1

    def order(self, *_):
        return Order.Any

    def alignment(self, *_) -> Collection:
        return self._target.keys()


class ContainsSubsetEvaluator(SubsetTargetEvaluator):
    """Whether the target is a subset of the generator."""

    def next_state(self, state, outcome, count):
        if state is None:
            state = True
        if self._target.get(outcome, 0) > count:
            state = False
        return state

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return True
        else:
            return final_state


class IntersectionSizeEvaluator(SubsetTargetEvaluator):
    """How many elements overlap between the generator and the target."""

    def next_state(self, state, outcome, count):
        if state is None:
            state = 0
        state += min(self._target.get(outcome, 0), count)
        return state

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return 0
        else:
            return final_state


class BestMatchingSetEvaluator(OutcomeCountEvaluator):
    """The best matching set of a generator.

    This prioritizes set size, then the outcome.

    The outcomes are `(set_size, outcome)`.
    """

    def next_state(self, state, outcome, count):
        """Replace the last best set if this one is better.

        Note the use of tuple comparison, which priortizes elements to the left.
        """
        if state is None:
            return count, outcome
        else:
            return max(state, (count, outcome))

    def order(self, *_):
        return Order.Any


best_matching_set_evaluator = BestMatchingSetEvaluator()


class BestStraightEvaluator(OutcomeCountEvaluator):
    """The best straight in a generator.

    Outcomes must be `int`s.

    This prioritizes run size, then the outcome.

    The outcomes are `(run_size, outcome)`.
    """

    def next_state(self, state, outcome, count):
        """Increments the current run if at least one `Die` rolled this outcome,
        then saves the run to the state.
        """
        best_run, best_run_outcome, run = state or (0, outcome, 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max((run, outcome), (best_run, best_run_outcome)) + (run,)

    def final_outcome(self, final_state, *_):
        return final_state[:2]

    def order(self, *_):
        return Order.Ascending

    alignment = OutcomeCountEvaluator.range_alignment


best_straight_evaluator = BestStraightEvaluator()