__docformat__ = 'google'

import operator
import icepool

import icepool.generator
from icepool.collection.counts import Counts
from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Order, Outcome, Qs, T

import bisect
import functools
import itertools
import random

from abc import ABC, abstractmethod
from functools import cached_property

from typing import Any, Callable, Collection, Generic, Hashable, Iterator, Mapping, Sequence, TypeAlias, cast

NextMultisetGenerator: TypeAlias = Iterator[tuple['icepool.MultisetGenerator',
                                                  Sequence, int]]
"""The generator type returned by `_generate_min` and `_generate_max`."""


class MultisetGenerator(Generic[T, Qs], MultisetExpression[T]):
    """Abstract base class for generating one or more multisets.

    These include dice pools (`Pool`) and card deals (`Deal`). Most likely you
    will be using one of these two rather than writing your own subclass of
    `MultisetGenerator`.

    The multisets are incrementally generated one outcome at a time.
    For each outcome, a `count` and `weight` are generated, along with a
    smaller generator to produce the rest of the multiset.

    You can perform simple evaluations using built-in operators and methods in
    this class.
    For more complex evaluations and better performance, particularly when
    multiple generators are involved, you will want to write your own subclass
    of `MultisetEvaluator`.
    """

    @abstractmethod
    def outcomes(self) -> Sequence[T]:
        """The possible outcomes that could be generated, in ascending order."""

    @abstractmethod
    def output_arity(self) -> int:
        """The number of multisets/counts generated. Must be constant."""

    @abstractmethod
    def _is_resolvable(self) -> bool:
        """`True` iff the generator is capable of producing an overall outcome.

        For example, a dice `Pool` will return `False` if it contains any dice
        with no outcomes.
        """

    @abstractmethod
    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
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
    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
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

    @property
    @abstractmethod
    def _key_tuple(self) -> tuple[Hashable, ...]:
        """A tuple that logically identifies this object among MultisetGenerators.

        Used to implement `equals()` and `__hash__()`
        """

    def equals(self, other) -> bool:
        """Whether this generator is logically equal to another object."""
        if not isinstance(other, MultisetGenerator):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash

    # Equality with truth value, needed for hashing.

    # The result has a truth value, but is not a bool.
    def __eq__(  # type: ignore
            self, other) -> 'icepool.DieWithTruth[bool]':

        def data_callback() -> Counts[bool]:
            die = cast('icepool.Die[bool]',
                       MultisetExpression.__eq__(self, other))
            if not isinstance(die, icepool.Die):
                raise TypeError('Did not resolve to a die.')
            return die._data

        def truth_value_callback() -> bool:
            if not isinstance(other, MultisetGenerator):
                return False
            return self._key_tuple == other._key_tuple

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    # The result has a truth value, but is not a bool.
    def __ne__(  # type: ignore
            self, other) -> 'icepool.DieWithTruth[bool]':

        def data_callback() -> Counts[bool]:
            die = cast('icepool.Die[bool]',
                       MultisetExpression.__ne__(self, other))
            if not isinstance(die, icepool.Die):
                raise TypeError('Did not resolve to a die.')
            return die._data

        def truth_value_callback() -> bool:
            if not isinstance(other, MultisetGenerator):
                return True
            return self._key_tuple != other._key_tuple

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    # Expression API.

    def _next_state(self, state, outcome: Outcome, *counts:
                    int) -> tuple[Hashable, int]:
        raise RuntimeError(
            'Internal error: Expressions should be unbound before evaluation.')

    def _order(self) -> Order:
        return Order.Any

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return (self,)

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_expression = icepool.expression.MultisetVariable(prefix_start)
        return unbound_expression, prefix_start + 1

    def _free_arity(self) -> int:
        return 0

    def min_outcome(self) -> T:
        return self.outcomes()[0]

    def max_outcome(self) -> T:
        return self.outcomes()[-1]

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
