"""Concrete subclasses of OutcomeCountEvaluator."""

__docformat__ = 'google'

import icepool
from icepool.constant import Order
from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator
from icepool.typing import Outcome

from collections import defaultdict
from functools import cached_property
from typing import Any, Callable, Collection, Container, Hashable, Mapping, MutableMapping, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""


class WrapFuncEvaluator(OutcomeCountEvaluator[T_contra, U_co]):
    """An `OutcomeCountEvaluator` created from a single provided function.

    `next_state()` simply calls that function.
    """

    def __init__(self, func: Callable[..., U_co], /):
        """Constructs a new instance given the function that should be called for `next_state()`.
        Args:
            func(state, outcome, *counts): This should take the same arguments
                as `next_state()`, minus `self`, and return the next state.
        """
        self._func = func

    def next_state(self, state: Hashable, outcome: T_contra, *counts: int):
        return self._func(state, outcome, *counts)


class JointEvaluator(OutcomeCountEvaluator[T_contra, tuple]):
    """An `OutcomeCountEvaluator` that jointly evaluates sub-evaluators on the same roll(s) of a generator."""

    def __init__(self, *sub_evaluators: OutcomeCountEvaluator):
        self._sub_evaluators = sub_evaluators

    def next_state(self, state, outcome, *counts: int):
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

    def order(self, *generators: icepool.OutcomeCountGenerator):
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
            return Order.Ascending
        elif descending:
            return Order.Descending
        else:
            return Order.Any


class SumEvaluator(OutcomeCountEvaluator):
    """Sums all outcomes."""

    def __init__(self,
                 *,
                 map: Callable[[Any], Any] | Mapping[Any, Any] | None = None):

        if map is None:
            self._map = lambda outcome: outcome
        elif callable(map):
            self._map = map
        else:
            # map is a Mapping.
            def map_final(outcome):
                return map.get(outcome, outcome)

            self._map = map_final

    def next_state(self, state, outcome, count):
        """Add the outcomes to the running total. """
        outcome = self._map(outcome)
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


class ExpandEvaluator(OutcomeCountEvaluator[Any, tuple]):
    """Expands all results of a generator.

    This is expensive and not recommended unless there are few possibilities.
    """

    def __init__(self, *, unique: bool = False):
        """
        Args:
            unique: Iff `True`, duplicate outcomes count only as one.
        """
        self._unique = unique

    def next_state(self, state, outcome, count):
        if count < 0:
            raise ValueError(
                'EnumerateGenerator is not compatible with negative counts.')
        if self._unique:
            count = min(count, 1)
        if state is None:
            return (outcome,) * count
        else:
            return state + (outcome,) * count

    def order(self, *_):
        return Order.Any

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return ()
        return tuple(sorted(final_state))


expand_evaluator = ExpandEvaluator()


class CountInEvaluator(OutcomeCountEvaluator[T_contra, int]):
    """Counts how many of the given outcomes are produced by the generator."""

    def __init__(self, target: Container[T_contra], /):
        self._target = target

    def next_state(self, state, outcome, count):
        if outcome in self._target:
            state = (state or 0) + count
        return state

    def final_outcome(self, final_state, *_):
        return final_state or 0

    def order(self, *_):
        return Order.Any


class CountUniqueEvaluator(OutcomeCountEvaluator[Any, int]):
    """Counts how many outcomes appeared more than zero times."""

    def next_state(self, state, _, count):
        return (state or 0) + (count > 0)

    def final_outcome(self, final_state, *_):
        return final_state or 0

    def order(self, *_):
        return Order.Any


count_unique_evaluator = CountUniqueEvaluator()


class SubsetTargetEvaluator(OutcomeCountEvaluator[T_contra, U_co]):
    """Base class for evaluators that look for a subset (possibly with repeated elements)."""

    def __init__(self, targets: Collection[T_contra] | Mapping[T_contra, int],
                 /):
        """
        Args:
            targets: Either a collection of outcomes, possibly with repeated elements.
                Or a mapping from outcomes to counts.
        """
        if isinstance(targets, Mapping):
            self._targets = targets
        else:
            self._targets = defaultdict(int)
            for outcome in targets:
                self._targets[outcome] += 1

    def order(self, *_):
        return Order.Any

    def alignment(self, *_) -> Collection:
        return set(self._targets.keys())


class ContainsSubsetEvaluator(SubsetTargetEvaluator[Any, bool]):
    """Whether the target is a subset of the generator."""

    def next_state(self, state, outcome, count):
        if state is None:
            state = True
        return state and count >= self._targets.get(outcome, count)

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return True
        else:
            return final_state


class IntersectionSizeEvaluator(SubsetTargetEvaluator[Any, int]):
    """How many elements overlap between the generator and the target."""

    def next_state(self, state, outcome, count):
        if state is None:
            state = 0
        return state + min(count, self._targets.get(outcome, 0))

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return 0
        return final_state


class LargestMatchingSetEvaluator(OutcomeCountEvaluator[Any, int]):
    """The largest matching set of a generator."""

    def next_state(self, state, _, count):
        return max(state or count, count)

    def order(self, *_):
        return Order.Any


class LargestMatchingSetAndOutcomeEvaluator(OutcomeCountEvaluator[Any,
                                                                  tuple[int,
                                                                        Any]]):

    def next_state(self, state, outcome, count):
        return max(state or (count, outcome), (count, outcome))

    def order(self, *_):
        return Order.Any


class AllMatchingSetsEvaluator(OutcomeCountEvaluator[Any, tuple[int, ...]]):
    """Produces the size of all matching sets of at least a given count."""

    def __init__(self, min_count=1):
        """
        Args:
            min_count: Outcomes with counts less than this will be ignored.
                If set to zero, the length of the resulting outcomes is
                constant.
        """
        self._min_count = min_count

    def next_state(self, state, outcome, count):
        if state is None:
            state = ()
        if count >= self._min_count:
            state = state + (count,)
        return state

    def order(self, *_):
        return Order.Any

    def final_outcome(self, final_state, /, *_):
        return tuple(sorted(final_state))


class LargestStraightEvaluator(OutcomeCountEvaluator[int, int]):

    def next_state(self, state, _, count):
        best_run, run = state or (0, 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max(best_run, run), run

    def final_outcome(self, final_state, *_):
        return final_state[0]

    def order(self, *_):
        return Order.Ascending

    alignment = OutcomeCountEvaluator.range_alignment


class LargestStraightAndOutcomeEvaluator(OutcomeCountEvaluator[int,
                                                               tuple[int,
                                                                     int]]):

    def next_state(self, state, outcome, count):
        best_run_and_outcome, run = state or ((0, outcome), 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        return max(best_run_and_outcome, (run, outcome)), run

    def final_outcome(self, final_state, *_):
        return final_state[0]

    def order(self, *_):
        return Order.Ascending

    alignment = OutcomeCountEvaluator.range_alignment
