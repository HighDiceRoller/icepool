__docformat__ = 'google'

import operator
import icepool
import icepool.generator
from icepool.collections import Counts
from icepool.typing import Outcome, SetComparatorStr

import bisect
import functools
import itertools
import random

from abc import ABC, abstractmethod

from typing import Any, Callable, Collection, Generic, Hashable, Iterator, Mapping, Sequence, TypeAlias, TypeVar

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""Type variable representing the outcome type."""

Q_co = TypeVar('Q_co', bound=tuple, covariant=True)
"""Type variable representing the counts type.

In this future this may be replaced with a TypeVarTuple."""

Qints_co = TypeVar('Qints_co', bound=tuple[int, ...], covariant=True)
"""Type variable representing the counts type, which is a tuple of `int`s.

In this future this may be replaced with a TypeVarTuple."""

U = TypeVar('U', bound=Outcome)
"""Type variable representing another outcome type."""

NextMultisetGenerator: TypeAlias = Iterator[tuple['icepool.MultisetGenerator',
                                                  Sequence, int]]
"""The generator type returned by `_generate_min` and `_generate_max`."""


def implicit_convert_to_generator(arg) -> 'MultisetGenerator':
    if isinstance(arg, MultisetGenerator):
        return arg
    elif isinstance(arg, (Mapping, Sequence)):
        if any(isinstance(k, icepool.Population) for k in arg):
            raise TypeError(
                'Only fixed multisets may be implicitly converted to a MultisetGenerator.'
            )
        return icepool.Pool(arg)
    else:
        raise TypeError(
            f'Argument of type {arg.__class__.__name__} cannot be implicitly converted to a MultisetGenerator.'
        )


class MultisetGenerator(ABC, Generic[T_co, Q_co]):
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
    def outcomes(self) -> Sequence[T_co]:
        """The set of outcomes, in sorted order."""

    @property
    @abstractmethod
    def arity(self) -> int:
        """The number of counts generated. Must be constant."""

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

    @functools.cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash

    def evaluate(self, evaluator: 'icepool.MultisetEvaluator[T_co, Any, U]',
                 /) -> 'icepool.Die[U]':
        """Evaluates this generator using the given `MultisetEvaluator`."""
        return evaluator.evaluate(self)

    def min_outcome(self) -> T_co:
        return self.outcomes()[0]

    def max_outcome(self) -> T_co:
        return self.outcomes()[-1]

    # Built-in evaluators.

    def expand(self) -> 'icepool.Die[tuple[T_co, ...]]':
        """All possible sorted tuples of outcomes.

        This is expensive and not recommended unless there are few possibilities.
        """
        return icepool.evaluator.ExpandEvaluator().evaluate(self)

    def sum(
        self,
        map: Callable[[T_co], U] | Mapping[T_co, U] | None = None
    ) -> 'icepool.Die[U]':
        """The sum of the outcomes.

        Args:
            map: If provided, the outcomes will be mapped according to this
                before summing.
        """
        return icepool.evaluator.SumEvaluator(map).evaluate(self)

    def count(self) -> 'icepool.Die[int]':
        """The total count over all outcomes.

        This is usually not very interesting unless some other operation is
        performed first. Examples:

        `generator.unique().count()` will count the number of unique outcomes.

        `(generator & [4, 5, 6]).count()` will count up to one each of
        4, 5, and 6.
        """
        return icepool.evaluator.count_evaluator.evaluate(self)

    def highest_outcome_and_count(self) -> 'icepool.Die[tuple[T_co, int]]':
        """The highest outcome with positive count, along with that count.

        If no outcomes have positive count, an arbitrary outcome will be
        produced with a 0 count.
        """
        return icepool.evaluator.HighestOutcomeAndCountEvaluator().evaluate(
            self)

    def all_counts(self,
                   positive_only: bool = True,
                   reverse=False) -> 'icepool.Die[tuple[int, ...]]':
        """Produces a tuple of all counts, i.e. the sizes of all matching sets.

        Args:
            positive_only: If `True` (default), negative and zero counts
                will be omitted.
            reversed: If `False` (default), the counts will be in ascending
                order. If `True`, they will be in descending order.
        """
        result = icepool.evaluator.AllCountsEvaluator(
            positive_only=positive_only).evaluate(self)

        if reverse:
            result = result.map(lambda x: tuple(reversed(x)))

        return result

    def largest_count(self) -> 'icepool.Die[int]':
        """The largest matching set among the outcomes.

        Returns:
            A `Die` with outcomes set_size.
            The greatest single such set is returned.
        """
        return icepool.evaluator.LargestCountEvaluator().evaluate(self)

    def largest_count_and_outcome(self) -> 'icepool.Die[tuple[int, T_co]]':
        """The largest matching set among the outcomes.

        Returns:
            A `Die` with outcomes (set_size, outcome).
            The greatest single such set is returned.
        """
        return icepool.evaluator.LargestCountAndOutcomeEvaluator().evaluate(
            self)

    def largest_straight(
            self: 'MultisetGenerator[int, tuple[int]]') -> 'icepool.Die[int]':
        """The best straight among the outcomes.

        Outcomes must be `int`s.

        Returns:
            A `Die` with outcomes straight_size.
            The greatest single such straight is returned.
        """
        return icepool.evaluator.LargestStraightEvaluator().evaluate(self)

    def largest_straight_and_outcome(
        self: 'MultisetGenerator[int, tuple[int]]'
    ) -> 'icepool.Die[tuple[int, int]]':
        """The best straight among the outcomes.

        Outcomes must be `int`s.

        Returns:
            A `Die` with outcomes (straight_size, outcome).
            The greatest single such straight is returned.
        """
        return icepool.evaluator.LargestStraightAndOutcomeEvaluator().evaluate(
            self)

    # Comparators.

    def compare(
            self: 'MultisetGenerator[T_co, tuple[int]]',
            op_name: SetComparatorStr, right:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Collection[T_co]',
            /) -> 'icepool.Die[bool]':
        """Compares the outcome multiset to another multiset.

        You can also use the symbolic operators directly, e.g.
        `generator <= [1, 2, 2]`.
        In this case, if the other argument is a `Mapping` or `Collection`, it
        will be converted into a generator automatically.

        Args:
            op_name: One of the following strings:
                `<, <=, >, >=, ==, !=, isdisjoint`.
            right: The right-side generator or multiset to compare with.
        """
        if isinstance(right, MultisetGenerator):
            return icepool.evaluator.ComparisonEvaluator.new_by_name(
                op_name).evaluate(self, right)  # type: ignore
        elif isinstance(right, (Mapping, Collection)):
            return icepool.evaluator.ComparisonEvaluator.new_by_name(
                op_name, right).evaluate(self)
        else:
            return NotImplemented

    def __lt__(
            self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Collection[T_co]',
            /) -> 'icepool.Die[bool]':
        return self.compare('<', other)

    def __le__(
            self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Collection[T_co]',
            /) -> 'icepool.Die[bool]':
        return self.compare('<=', other)

    def issubset(
            self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Collection[T_co]',
            /) -> 'icepool.Die[bool]':
        """Whether the outcome multiset is a subset of the other multiset.

        Same as `self <= other`.
        """
        return self <= other

    def __gt__(
            self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Collection[T_co]',
            /) -> 'icepool.Die[bool]':
        return self.compare('>', other)

    def __ge__(
            self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Collection[T_co]',
            /) -> 'icepool.Die[bool]':
        return self.compare('>=', other)

    def issuperset(
            self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Collection[T_co]',
            /) -> 'icepool.Die[bool]':
        """Whether the outcome multiset is a superset of the target multiset.

        Same as `self >= other`.
        """
        return self >= other

    # The result has a truth value, but is not a bool.
    def __eq__(self, other) -> 'icepool.DieWithTruth[bool]':  # type: ignore

        def data_callback() -> 'Counts[bool]':
            # May fail if types are incompatible.
            return self.compare('==', other)._data  # type: ignore

        def truth_value_callback() -> bool:
            return self.equals(other)

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    # The result has a truth value, but is not a bool.
    def __ne__(self, other) -> 'icepool.DieWithTruth[bool]':  # type: ignore

        def data_callback() -> 'Counts[bool]':
            # May fail if types are incompatible.
            return self.compare('!=', other)._data  # type: ignore

        def truth_value_callback() -> bool:
            return not self.equals(other)

        return icepool.DieWithTruth(data_callback, truth_value_callback)

    def isdisjoint(
            self: 'MultisetGenerator[T_co, tuple[int]]', right:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Collection[T_co]',
            /) -> 'icepool.Die[bool]':
        """Whether the outcome multiset is disjoint from the target multiset."""
        result = self.compare('isdisjoint', right)
        if result is NotImplemented:
            raise TypeError(
                f'Cannot evaluate with right side of type {right.__class__.__name__}.'
            )
        return result

    # Binary operations with other generators.

    def binary_operator(
        self: 'MultisetGenerator[T_co, tuple[int]]', op: Callable,
        right: 'MultisetGenerator[T_co, tuple[int]]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        """Binary operation with another generator.

        You can also use the symbolic operators directly, e.g.
        `generator & [1, 2, 2]`.
        In this case, if the other argument is a `Mapping` or `Sequence`, it
        will be converted into a generator automatically.

        Args:
            op_name: One of the following strings:
                `+, -, |, &, ^`.
            right: The other `MultisetGenerator`.
        """
        from icepool.expression import multiset_variables, ExpressionGenerator
        expression = op(multiset_variables[0], multiset_variables[1])
        return ExpressionGenerator(self, right, expression=expression)

    def __add__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return self.binary_operator(operator.add, other_generator)

    def __radd__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return other_generator.binary_operator(operator.add, self)

    def disjoint_sum(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        """The multiset disjoint sum with another generator.

        Same as `self + other`.
        """
        return self + other

    def __sub__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return self.binary_operator(operator.sub, other_generator)

    def __rsub__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return other_generator.binary_operator(operator.sub, self)

    def difference(
        self: 'MultisetGenerator[T_co, tuple[int]]', *others:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        """The multiset difference with another generator(s).

        Same as `self - other - ...`.
        """
        return functools.reduce(operator.sub, others, self)  # type: ignore

    def __or__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return self.binary_operator(operator.or_, other_generator)

    def __ror__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return other_generator.binary_operator(operator.or_, self)

    def union(
        self: 'MultisetGenerator[T_co, tuple[int]]', *others:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        """The multiset union with another generator.

        Same as `self | other | ...`.
        """
        return functools.reduce(operator.or_, others, self)  # type: ignore

    def __and__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return self.binary_operator(operator.and_, other_generator)

    def __rand__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return other_generator.binary_operator(operator.and_, self)

    def intersection(
        self: 'MultisetGenerator[T_co, tuple[int]]', *others:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        """The multiset intersection with another generator.

        Same as `self & other & ...`.
        """
        return functools.reduce(operator.and_, others, self)  # type: ignore

    def __xor__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return self.binary_operator(operator.xor, other_generator)

    def __rxor__(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        other_generator = implicit_convert_to_generator(other)
        return other_generator.binary_operator(operator.xor, self)

    def symmetric_difference(
        self: 'MultisetGenerator[T_co, tuple[int]]', other:
        'MultisetGenerator[T_co, tuple[int]] | Mapping[T_co, int] | Sequence[T_co]'
    ) -> 'MultisetGenerator[T_co, tuple[int]]':
        """The multiset symmetric difference with another generator.

        Same as `self ^ other`.
        """
        return self ^ other

    # Count adjustment.

    def binary_int_operator(
            self: 'MultisetGenerator[T_co, Qints_co]', op: Callable,
            constant: int) -> 'MultisetGenerator[T_co, Qints_co]':
        """Binary operation with an integer. These adjust counts.

        Args:
            op_name: One of the following strings:
                `*, //`.
            constant: An `int`.
        """
        if isinstance(constant, int):
            from icepool.expression import multiset_variables, MapExpressionGenerator
            expression = op(multiset_variables[0], constant)
            return MapExpressionGenerator(self, expression)  # type: ignore
        else:
            return NotImplemented

    def __mul__(self: 'MultisetGenerator[T_co, Qints_co]',
                constant: int) -> 'MultisetGenerator[T_co, Qints_co]':
        return self.binary_int_operator(operator.mul, constant)

    # Commutable in this case.
    def __rmul__(self: 'MultisetGenerator[T_co, Qints_co]',
                 constant: int) -> 'MultisetGenerator[T_co, Qints_co]':
        return self.binary_int_operator(operator.mul, constant)

    def multiply_counts(self: 'MultisetGenerator[T_co, Qints_co]',
                        constant: int) -> 'MultisetGenerator[T_co, Qints_co]':
        """Multiplies all counts by a constant.

        Same as `self * constant`.
        """
        return self * constant

    def __floordiv__(self: 'MultisetGenerator[T_co, Qints_co]',
                     constant: int) -> 'MultisetGenerator[T_co, Qints_co]':
        return self.binary_int_operator(operator.floordiv, constant)

    def divide_counts(self: 'MultisetGenerator[T_co, Qints_co]',
                      constant: int) -> 'MultisetGenerator[T_co, Qints_co]':
        """Divides all counts (rounding down).

        Same as `self // constant`.
        """
        return self // constant

    def filter_counts(self: 'MultisetGenerator[T_co, Qints_co]',
                      min_count: int) -> 'MultisetGenerator[T_co, Qints_co]':
        """Counts less than `min_count` are treated as zero.

        For example, `generator.filter_counts(2)` would only produce
        pairs and better.
        """
        from icepool.expression import multiset_variables, MapExpressionGenerator, FilterCountsExpression
        expression = FilterCountsExpression(multiset_variables[0], min_count)
        return MapExpressionGenerator(self, expression)  # type: ignore

    def unique(self: 'MultisetGenerator[T_co, Qints_co]',
               max_count: int = 1) -> 'MultisetGenerator[T_co, Qints_co]':
        """Counts each outcome at most `max_count` times.

        For example, `generator.unique(2)` would count each outcome at most
        twice.
        """
        from icepool.expression import multiset_variables, MapExpressionGenerator, UniqueExpression
        expression = UniqueExpression(multiset_variables[0], max_count)
        return MapExpressionGenerator(self, expression)  # type: ignore

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
