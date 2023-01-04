__docformat__ = 'google'

import icepool
from icepool.constant import Order
from icepool.typing import Outcome

import bisect
import itertools
import random

from abc import ABC, abstractmethod

from typing import Any, Callable, Collection, Container, Generic, Hashable, Iterator, Mapping, Sequence, Set, TypeAlias, TypeVar

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""Type variable representing the outcome type."""

U = TypeVar('U', bound=Outcome)
"""Type variable representing another outcome type."""

NextOutcomeCountGenerator: TypeAlias = Iterator[tuple[
    'icepool.OutcomeCountGenerator', Sequence, int]]
"""The generator type returned by `_generate_min` and `_generate_max`."""


class OutcomeCountGenerator(ABC, Generic[T_co]):
    """Abstract base class for incrementally generating `(outcome, counts, weight)`s.

    These include dice pools (`Pool`) and card deals (`Deal`). Most likely you
    will be using one of these two rather than writing your own subclass of
    `OutcomeCountGenerator`.

    These generators can be evaluated by an `OutcomeCountEvaluator`, which you
    *are* likely to write your own concrete subclass of.
    """

    @abstractmethod
    def outcomes(self) -> Sequence[T_co]:
        """The set of outcomes, in sorted order."""

    @abstractmethod
    def counts_len(self) -> int:
        """The number of counts generated. Must be constant."""

    @abstractmethod
    def _is_resolvable(self) -> bool:
        """`True` iff the generator is capable of producing an overall outcome.

        For example, a dice `Pool` will return `False` if it contains any dice
        with no outcomes.
        """

    @abstractmethod
    def _generate_min(self, min_outcome) -> NextOutcomeCountGenerator:
        """Pops the min outcome from this generator if it matches the argument.

        Yields:
            * A generator with the min outcome popped.
            * A tuple of counts for the min outcome.
            * The weight for this many of the min outcome appearing.

            If the argument does not match the min outcome, or this generator
            has no outcomes, only a single tuple is yielded:

            * `self`
            * A tuple of zeros.
            * weight = 1.
        """

    @abstractmethod
    def _generate_max(self, max_outcome) -> NextOutcomeCountGenerator:
        """Pops the max outcome from this generator if it matches the argument.

        Yields:
            * A generator with the min outcome popped.
            * A tuple of counts for the min outcome.
            * The weight for this many of the min outcome appearing.

            If the argument does not match the min outcome, or this generator
            has no outcomes, only a single tuple is yielded:

            * `self`
            * A tuple of zeros.
            * weight = 1.
        """

    @abstractmethod
    def _estimate_order_costs(self) -> tuple[int, int]:
        """Estimates the cost of popping from the min and max sides during an evaluation.

        Returns:
            pop_min_cost: A positive `int`.
            pop_max_cost: A positive `int`.
        """

    @abstractmethod
    def denominator(self) -> int:
        """The total weight of all paths through this generator."""

    @abstractmethod
    def __eq__(self, other) -> bool:
        """All `OutcomeCountGenerator`s must implement equality."""

    @abstractmethod
    def __hash__(self) -> int:
        """All `OutcomeCountGenerator`s must be hashable."""

    def evaluate(self,
                 evaluator_or_func: 'icepool.OutcomeCountEvaluator[Any, U, Any]'
                 | Callable[..., U], /) -> 'icepool.Die[U]':
        """Evaluates this generator using the given `OutcomeCountEvaluator` or function.

        Note that each `OutcomeCountEvaluator` instance carries its own cache;
        if you plan to use an evaluation multiple times,
        you may want to explicitly create an `OutcomeCountEvaluator` instance
        rather than passing a function to this method directly.

        Args:
            func: This can be an `OutcomeCountEvaluator`, in which case it evaluates
                the generator directly.
                Or it can be a `OutcomeCountEvaluator.next_state()`-like
                function, taking in `state, outcome, *counts` and returning the
                next state. In this case a temporary `WrapFuncEvaluator`
                is constructed and used to evaluate this generator.
        """
        from icepool.evaluator import WrapFuncEvaluator
        if not isinstance(evaluator_or_func, icepool.OutcomeCountEvaluator):
            evaluator_or_func = WrapFuncEvaluator(evaluator_or_func)
        return evaluator_or_func.evaluate(self)

    def min_outcome(self) -> T_co:
        return self.outcomes()[0]

    def max_outcome(self) -> T_co:
        return self.outcomes()[-1]

    # Built-in evaluators.

    def expand(self,
               target: Mapping[Outcome, int] | Set[Outcome] |
               Collection[Outcome] | None = None,
               *,
               invert: bool = False,
               min_count: int | None = None,
               div_count: int | None = None,
               max_count: int | None = None) -> 'icepool.Die[tuple[T_co, ...]]':
        """All possible sorted tuples of outcomes.

        This is expensive and not recommended unless there are few possibilities.
        """
        from icepool.evaluator import AdjustIntCountEvaluator, ExpandEvaluator
        return AdjustIntCountEvaluator(ExpandEvaluator(),
                                       target=target,
                                       invert=invert,
                                       min_count=min_count,
                                       div_count=div_count,
                                       max_count=max_count).evaluate(self)

    def sum(
        self,
        target: Mapping[Outcome, int] | Set[Outcome] | Collection[Outcome] |
        None = None,
        *,
        invert: bool = False,
        min_count: int | None = None,
        div_count: int | None = None,
        max_count: int | None = None,
        map: Callable[[T_co], U] | Mapping[T_co, U] | None = None
    ) -> 'icepool.Die[U]':
        """The sum of the outcomes.

        Args:
            map: If provided, the outcomes will be mapped according to this
                before summing.
        """
        from icepool.evaluator import AdjustIntCountEvaluator, FinalOutcomeMapEvaluator, sum_evaluator
        return AdjustIntCountEvaluator(FinalOutcomeMapEvaluator(
            sum_evaluator, map),
                                       target=target,
                                       invert=invert,
                                       min_count=min_count,
                                       div_count=div_count,
                                       max_count=max_count).evaluate(self)

    def count(self,
              target: Mapping[Outcome, int] | Set[Outcome] |
              Collection[Outcome] | None = None,
              *,
              invert: bool = False,
              min_count: int | None = None,
              div_count: int | None = None,
              max_count: int | None = None) -> 'icepool.Die[int]':
        """The number of outcomes that are == the target.

        If no target is provided, all outcomes will be counted.
        """
        from icepool.evaluator import AdjustIntCountEvaluator, count_evaluator
        return AdjustIntCountEvaluator(count_evaluator,
                                       target=target,
                                       invert=invert,
                                       min_count=min_count,
                                       div_count=div_count,
                                       max_count=max_count).evaluate(self)

    def largest_matching_set(self) -> 'icepool.Die[int]':
        """The largest matching set among the outcomes.

        Returns:
            A `Die` with outcomes set_size.
            The greatest single such set is returned.
        """
        from icepool.evaluator import LargestMatchingSetEvaluator
        return LargestMatchingSetEvaluator().evaluate(self)

    def largest_matching_set_and_outcome(
            self) -> 'icepool.Die[tuple[int, T_co]]':
        """The largest matching set among the outcomes.

        Returns:
            A `Die` with outcomes (set_size, outcome).
            The greatest single such set is returned.
        """
        from icepool.evaluator import LargestMatchingSetAndOutcomeEvaluator
        return LargestMatchingSetAndOutcomeEvaluator().evaluate(self)

    def all_matching_sets(
            self,
            target: Mapping[Outcome, int] | Set[Outcome] | Collection[Outcome] |
        None = None,
            *,
            invert: bool = False,
            min_count: int | None = None,
            div_count: int | None = None,
            max_count: int | None = None,
            positive_only: bool = True,
            order: Order = Order.Ascending) -> 'icepool.Die[tuple[int, ...]]':
        """Produces the size of all matching sets of at least a given count.

        Args:
            min_count: Outcomes with counts less than this will be ignored.
                If set to zero, the length of the resulting outcomes is
                constant.
            order: The order in which the set sizes will be presented.
        """
        from icepool.evaluator import AdjustIntCountEvaluator, AllMatchingSetsEvaluator
        result = AdjustIntCountEvaluator(
            AllMatchingSetsEvaluator(positive_only=positive_only),
            target=target,
            invert=invert,
            min_count=min_count,
            div_count=div_count,
            max_count=max_count).evaluate(self)

        if order < 0:
            result = result.map(lambda x: tuple(reversed(x)))

        return result

    def largest_straight(
            self: 'OutcomeCountGenerator[int]') -> 'icepool.Die[int]':
        """The best straight among the outcomes.

        Outcomes must be `int`s.

        Returns:
            A `Die` with outcomes straight_size.
            The greatest single such straight is returned.
        """
        from icepool.evaluator import LargestStraightEvaluator
        return LargestStraightEvaluator().evaluate(self)

    def largest_straight_and_outcome(
            self: 'OutcomeCountGenerator[int]'
    ) -> 'icepool.Die[tuple[int, int]]':
        """The best straight among the outcomes.

        Outcomes must be `int`s.

        Returns:
            A `Die` with outcomes (straight_size, outcome).
            The greatest single such straight is returned.
        """
        from icepool.evaluator import LargestStraightAndOutcomeEvaluator
        return LargestStraightAndOutcomeEvaluator().evaluate(self)

    # Sampling.

    def sample(self) -> tuple[tuple, ...]:
        """EXPERIMENTAL: A single random sample from this generator.

        This uses the standard `random` package and is not cryptographically
        secure.

        Returns:
            A sorted tuple of outcomes for each output of this generator.
        """
        if not self.outcomes():
            raise ValueError('Cannot sample from an empty set of outcomes.')

        min_cost, max_cost = self._estimate_order_costs()

        if min_cost < max_cost:
            outcome = self.min_outcome()
            generated = tuple(self._generate_min(outcome))
        else:
            outcome = self.max_outcome()
            generated = tuple(self._generate_max(outcome))

        cumulative_weights = tuple(
            itertools.accumulate(g.denominator() * w for g, _, w in generated))
        denominator = cumulative_weights[-1]
        # We don't use random.choices since that is based on floats rather than ints.
        r = random.randrange(denominator)
        index = bisect.bisect_right(cumulative_weights, r)
        popped_generator, counts, _ = generated[index]
        head = tuple((outcome,) * count for count in counts)
        if popped_generator.outcomes():
            tail = popped_generator.sample()
            return tuple(tuple(sorted(h + t)) for h, t, in zip(head, tail))
        else:
            return head
