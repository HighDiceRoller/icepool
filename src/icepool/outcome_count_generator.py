__docformat__ = 'google'

import icepool

import bisect
import itertools
import random

from abc import ABC, abstractmethod

from typing import Callable, Generator, Sequence, TypeAlias, TypeVar

NextOutcomeCountGenerator: TypeAlias = Generator[tuple['OutcomeCountGenerator',
                                                       Sequence[int], int],
                                                 None, None]
"""The generator type returned by `_generate_min` and `_generate_max`."""


class OutcomeCountGenerator(ABC):
    """Abstract base class for incrementally generating `(outcome, counts, weight)`s.

    These include dice pools (`Pool`) and card decks (`Deck`).

    These generators can be evaluated by an `OutcomeCountEvaluator`.
    """

    @abstractmethod
    def outcomes(self) -> Sequence:
        """The set of outcomes, in sorted order."""

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
            A generator with the min outcome popped.
            A tuple of counts for the min outcome.
            The weight for this many of the min outcome appearing.

            If the argument does not match the min outcome, or this generator
            has no outcomes, only the single tuple `(self, 0, 1)` is yielded.
        """

    @abstractmethod
    def _generate_max(self, max_outcome) -> NextOutcomeCountGenerator:
        """Pops the max outcome from this generator if it matches the argument.

        Yields:
            A generator with the max outcome popped.
            A tuple of counts for the max outcome.
            The weight for this many of the max outcome appearing.

            If the argument does not match the max outcome, or this generator
            has no outcomes, only the single tuple `(self, 0, 1)` is yielded.
        """

    @abstractmethod
    def _estimate_direction_costs(self) -> tuple[int, int]:
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
                 evaluator_or_func: 'icepool.OutcomeCountEvaluator' | Callable,
                 /) -> 'icepool.Die':
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
        if not isinstance(evaluator_or_func, icepool.OutcomeCountEvaluator):
            evaluator_or_func = icepool.WrapFuncEvaluator(evaluator_or_func)
        return evaluator_or_func.evaluate(self)

    def min_outcome(self):
        return self.outcomes()[0]

    def max_outcome(self):
        return self.outcomes()[-1]

    def sum(self) -> 'icepool.Die':
        """Convenience method to simply sum the dice in this generator.

        This uses `icepool.sum_pool`.

        Returns:
            A `Die` representing the sum.
        """
        return icepool.evaluate_sum(self)

    def sample(self) -> tuple[tuple, ...]:
        """EXPERIMENTAL: A single random sample from this generator.

        This uses the standard `random` package and is not cryptographically
        secure.

        Returns:
            A sorted tuple of outcomes for each output of this generator.
        """
        if not self.outcomes():
            raise ValueError('Cannot sample from an empty set of outcomes.')

        min_cost, max_cost = self._estimate_direction_costs()

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
