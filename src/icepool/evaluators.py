"""Concrete subclasses of OutcomeCountEvaluator."""

__docformat__ = 'google'

import icepool
from icepool.outcome_count_evaluator import Order, OutcomeCountEvaluator

from collections import defaultdict
from functools import cached_property
from typing import Any, Callable, Collection, Container, Hashable, Mapping, MutableMapping


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

    def order(self, *generators: icepool.OutcomeCountGenerator) -> Order:
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


class ExpandEvaluator(OutcomeCountEvaluator):
    """Expands all results of a generator.

    This is expensive and not recommended unless there are few possibilities.
    """

    def __init__(self, *, unique=False):
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


class CountInEvaluator(OutcomeCountEvaluator):
    """Counts how many of the given outcomes are produced by the generator."""

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


class CountUniqueEvaluator(OutcomeCountEvaluator):
    """Counts how many outcomes appeared more than zero times."""

    def next_state(self, state, _, count):
        return (state or 0) + (count > 0)

    def final_outcome(self, final_state, *_):
        return final_state or 0

    def order(self, *_):
        return Order.Any


count_unique_evaluator = CountUniqueEvaluator()


class SubsetTargetEvaluator(OutcomeCountEvaluator):
    """Base class for evaluators that look for a subset (possibly with repeated elements)."""

    def __init__(self,
                 targets: Collection | Mapping[Any, int],
                 /,
                 *,
                 wilds: Collection = ()):
        """
        Args:
            targets: Either a collection of outcomes, possibly with repeated elements.
                Or a mapping from outcomes to counts.
            wilds: EXPERIMENTAL: A collection of outcomes to treat as wilds.
                This API is likely to change in the future.
        """
        if isinstance(targets, Mapping):
            self._targets = targets
        else:
            self._targets = defaultdict(int)
            for outcome in targets:
                self._targets[outcome] += 1
        self._wilds = frozenset(wilds)

    def next_state(self, state, outcome, count):
        # The state is the number of extra wilds.
        # If positive, all targets were hit and there were wilds left over.
        # If zero, the number of wilds was exactly enough to hit the targets.
        # If negative, that number of targets are left after wilds.
        state = state or 0
        if outcome in self._wilds:
            state -= self._targets.get(outcome, 0) - count
        else:
            state -= max(self._targets.get(outcome, 0) - count, 0)
        return state

    def order(self, *_):
        return Order.Any

    def alignment(self, *_) -> Collection:
        return set(self._targets.keys()) | self._wilds


class ContainsSubsetEvaluator(SubsetTargetEvaluator):
    """Whether the target is a subset of the generator."""

    def final_outcome(self, final_state, *_):
        return (final_state or 0) >= 0


class IntersectionSizeEvaluator(SubsetTargetEvaluator):
    """How many elements overlap between the generator and the target."""

    def final_outcome(self, final_state, *_):
        return sum(self._targets.values()) + min(final_state, 0)


class BestMatchingSetEvaluator(OutcomeCountEvaluator):
    """The largest matching set of a generator."""

    def __init__(self, *, include_outcome=False, wilds: Collection = ()):
        """
        Args:
            include_outcome: If `True`, the final outcomes will be tuples
                `(set_size, outcome)`. Greater outcomes will be prioritized.
                If `False` the final outcomes will just be `set_size`.
        """
        self._include_outcome = include_outcome
        self._wilds = frozenset(wilds)

    def next_state(self, state, outcome, count):
        """Replace the last best set if this one is better.

        Note the use of tuple comparison, which priortizes elements to the left.
        """
        if count < 0:
            raise ValueError(
                'BestMatchingSetEvaluator is not compatible with negative counts.'
            )

        best_count, best_outcome, wild_count = state or (0, outcome, 0)

        if outcome in self._wilds:
            wild_count += count
            return best_count, best_outcome, wild_count

        if not self._include_outcome:
            best_outcome = None
            outcome = None

        best_count, best_outcome = max((best_count, best_outcome),
                                       (count, outcome))

        return best_count, best_outcome, wild_count

    def final_outcome(self, final_state, gen):
        best_count, best_outcome, wild_count = final_state

        if best_count == 0:
            best_outcome = gen.max_outcome()

        if self._include_outcome:
            return (best_count + wild_count), best_outcome
        else:
            return best_count + wild_count

    def order(self, *_):
        return Order.Any


class BestStraightEvaluator(OutcomeCountEvaluator):
    """The best straight in a generator.

    Outcomes must be `int`s.

    This prioritizes run size, then the outcome.
    """

    def __init__(self, *, include_outcome=False):
        """
        Args:
            include_outcome: If `True`, the final outcomes will be tuples
                `(straight_size, outcome)`. Greater outcomes will be
                prioritized, and the result is the greatest outcome in the
                straight.
                If `False`, the final outcomes will be just the straight size.
        """
        self._include_outcome = include_outcome

    def next_state(self, state, outcome, count):
        """Increments the current run if at least one `Die` rolled this outcome,
        then saves the run to the state.
        """
        best_run, best_run_outcome, run = state or (0, outcome, 0)
        if count >= 1:
            run += 1
        else:
            run = 0
        if not self._include_outcome:
            best_run_outcome = None
            outcome = None
        return max((run, outcome), (best_run, best_run_outcome)) + (run,)

    def final_outcome(self, final_state, *_):
        if self._include_outcome:
            return final_state[:2]
        else:
            return final_state[0]

    def order(self, *_):
        return Order.Ascending

    alignment = OutcomeCountEvaluator.range_alignment
