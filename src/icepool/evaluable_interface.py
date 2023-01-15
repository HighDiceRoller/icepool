__docformat__ = 'google'

import icepool

import functools
import operator

from icepool.typing import Evaluable, Outcome
from typing import TYPE_CHECKING, Callable, Generic, Mapping, Sequence, Type, TypeVar

if TYPE_CHECKING:
    from icepool.expression.fully_bound_expression import FullyBoundExpression

T = TypeVar('T', bound=Outcome)
"""An outcome type."""

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""An outcome type."""

U = TypeVar('U', bound=Outcome)
"""Another outcome type."""


class EvaluableInterface(Generic[T_co]):
    """Interface shared by evaluable types, namely `MultisetGenerator` and `GeneratorsWithExpression."""

    # Count adjustment.

    def __mul__(self: 'Evaluable[T_co]',
                constant: int) -> 'FullyBoundExpression[T_co]':
        return adjust_counts(self, constant,
                             icepool.expression.MultiplyCountsExpression)

    def __rmul__(self: 'Evaluable[T_co]',
                 constant: int) -> 'FullyBoundExpression[T_co]':
        # Commutable in this case.
        return adjust_counts(self, constant,
                             icepool.expression.MultiplyCountsExpression)

    def multiply_counts(self: 'Evaluable[T_co]',
                        constant: int) -> 'FullyBoundExpression[T_co]':
        return adjust_counts(self, constant,
                             icepool.expression.MultiplyCountsExpression)

    def __floordiv__(self: 'Evaluable[T_co]',
                     constant: int) -> 'FullyBoundExpression[T_co]':
        return adjust_counts(self, constant,
                             icepool.expression.FloorDivCountsExpression)

    def divide_counts(self: 'Evaluable[T_co]',
                      constant: int) -> 'FullyBoundExpression[T_co]':
        """Divides all counts (rounding down).

        Same as `self // constant`.
        """
        return adjust_counts(self, constant,
                             icepool.expression.FloorDivCountsExpression)

    def filter_counts(self: 'Evaluable[T_co]',
                      min_count: int) -> 'FullyBoundExpression[T_co]':
        """Counts less than `min_count` are treated as zero.

        For example, `generator.filter_counts(2)` would only produce
        pairs and better.
        """
        return adjust_counts(self, min_count,
                             icepool.expression.FilterCountsExpression)

    def unique(self: 'Evaluable[T_co]',
               max_count: int = 1) -> 'FullyBoundExpression[T_co]':
        """Counts each outcome at most `max_count` times.

        For example, `generator.unique(2)` would count each outcome at most
        twice.
        """
        return adjust_counts(self, max_count,
                             icepool.expression.UniqueExpression)

    # Binary operators.

    def __add__(self: 'Evaluable[T_co]',
                other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(self, other,
                                    icepool.expression.DisjointUnionExpression)
        except TypeError:
            return NotImplemented

    def disjoint_union(
            self: 'Evaluable[T_co]',
            *others: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        """The multiset disjoint sum with another generator.

        Same as `self + other + ...`.
        """
        return functools.reduce(operator.add, others, self)  # type: ignore

    def __radd__(self: 'Evaluable[T_co]',
                 other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(other, self,
                                    icepool.expression.DisjointUnionExpression)
        except TypeError:
            return NotImplemented

    def __sub__(self: 'Evaluable[T_co]',
                other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(self, other,
                                    icepool.expression.DifferenceExpression)
        except TypeError:
            return NotImplemented

    def difference(self: 'Evaluable[T_co]',
                   *others: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        """The multiset difference with another generator(s).

        Same as `self - other - ...`.
        """
        return functools.reduce(operator.sub, others, self)  # type: ignore

    def __rsub__(self: 'Evaluable[T_co]',
                 other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(other, self,
                                    icepool.expression.DifferenceExpression)
        except TypeError:
            return NotImplemented

    def __and__(self: 'Evaluable[T_co]',
                other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(self, other,
                                    icepool.expression.IntersectionExpression)
        except TypeError:
            return NotImplemented

    def intersection(
            self: 'Evaluable[T_co]',
            *others: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        """The multiset intersection with another generator.

        Same as `self & other & ...`.
        """
        return functools.reduce(operator.and_, others, self)  # type: ignore

    def __rand__(self: 'Evaluable[T_co]',
                 other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(other, self,
                                    icepool.expression.IntersectionExpression)
        except TypeError:
            return NotImplemented

    def __or__(self: 'Evaluable[T_co]',
               other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(self, other,
                                    icepool.expression.UnionExpression)
        except TypeError:
            return NotImplemented

    def union(self: 'Evaluable[T_co]',
              *others: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        """The multiset union with another generator.

        Same as `self | other | ...`.
        """
        return functools.reduce(operator.or_, others, self)  # type: ignore

    def __ror__(self: 'Evaluable[T_co]',
                other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(other, self,
                                    icepool.expression.UnionExpression)
        except TypeError:
            return NotImplemented

    def __xor__(self: 'Evaluable[T_co]',
                other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(
                self, other, icepool.expression.SymmetricDifferenceExpression)
        except TypeError:
            return NotImplemented

    def symmetric_difference(
            self: 'Evaluable[T_co]',
            other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        """The multiset symmetric difference with another generator.

        Same as `self ^ other`.
        """
        return binary_operation(
            self, other, icepool.expression.SymmetricDifferenceExpression)

    def __rxor__(self: 'Evaluable[T_co]',
                 other: 'Evaluable[T_co]') -> 'FullyBoundExpression[T_co]':
        try:
            return binary_operation(
                other, self, icepool.expression.SymmetricDifferenceExpression)
        except TypeError:
            return NotImplemented

    # Evaluators.

    def evaluate(self: 'Evaluable[T_co]',
                 evaluator: 'icepool.MultisetEvaluator[T_co, U]',
                 /) -> 'icepool.Die[U]':
        """Evaluates this generator using the given `MultisetEvaluator`."""
        return evaluator.evaluate(self)

    def expand(self: 'Evaluable[T_co]') -> 'icepool.Die[tuple[T_co, ...]]':
        """All possible sorted tuples of outcomes.

        This is expensive and not recommended unless there are few possibilities.
        """
        return icepool.evaluator.ExpandEvaluator().evaluate(self)

    def sum(
        self: 'Evaluable[T_co]',
        map: Callable[[T_co], U] | Mapping[T_co, U] | None = None
    ) -> 'icepool.Die[U]':
        """The sum of the outcomes.

        Args:
            map: If provided, the outcomes will be mapped according to this
                before summing.
        """
        return icepool.evaluator.SumEvaluator(map).evaluate(self)

    def count(self: 'Evaluable[T_co]') -> 'icepool.Die[int]':
        """The total count over all outcomes.

        This is usually not very interesting unless some other operation is
        performed first. Examples:

        `generator.unique().count()` will count the number of unique outcomes.

        `(generator & [4, 5, 6]).count()` will count up to one each of
        4, 5, and 6.
        """
        return icepool.evaluator.count_evaluator.evaluate(self)

    def highest_outcome_and_count(
            self: 'Evaluable[T_co]') -> 'icepool.Die[tuple[T_co, int]]':
        """The highest outcome with positive count, along with that count.

        If no outcomes have positive count, an arbitrary outcome will be
        produced with a 0 count.
        """
        return icepool.evaluator.HighestOutcomeAndCountEvaluator().evaluate(
            self)

    def all_counts(self: 'Evaluable[T_co]',
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

    def largest_count(self: 'Evaluable[T_co]') -> 'icepool.Die[int]':
        """The largest matching set among the outcomes.

        Returns:
            A `Die` with outcomes set_size.
            The greatest single such set is returned.
        """
        return icepool.evaluator.LargestCountEvaluator().evaluate(self)

    def largest_count_and_outcome(
            self: 'Evaluable[T_co]') -> 'icepool.Die[tuple[int, T_co]]':
        """The largest matching set among the outcomes.

        Returns:
            A `Die` with outcomes (set_size, outcome).
            The greatest single such set is returned.
        """
        return icepool.evaluator.LargestCountAndOutcomeEvaluator().evaluate(
            self)

    def largest_straight(self: 'Evaluable[int]') -> 'icepool.Die[int]':
        """The best straight among the outcomes.

        Outcomes must be `int`s.

        Returns:
            A `Die` with outcomes straight_size.
            The greatest single such straight is returned.
        """
        return icepool.evaluator.LargestStraightEvaluator().evaluate(self)

    def largest_straight_and_outcome(
            self: 'Evaluable[int]') -> 'icepool.Die[tuple[int, int]]':
        """The best straight among the outcomes.

        Outcomes must be `int`s.

        Returns:
            A `Die` with outcomes (straight_size, outcome).
            The greatest single such straight is returned.
        """
        return icepool.evaluator.LargestStraightAndOutcomeEvaluator().evaluate(
            self)

    # Comparators.

    def __lt__(self: 'Evaluable[T_co]', other: 'Evaluable[T_co]',
               /) -> 'icepool.Die[bool]':
        try:
            return compare(self, other,
                           icepool.evaluator.IsProperSubsetEvaluator)
        except TypeError:
            return NotImplemented

    def __le__(self: 'Evaluable[T_co]', other: 'Evaluable[T_co]',
               /) -> 'icepool.Die[bool]':
        try:
            return compare(self, other, icepool.evaluator.IsSubsetEvaluator)
        except TypeError:
            return NotImplemented

    def issubset(self: 'Evaluable[T_co]', other: 'Evaluable[T_co]',
                 /) -> 'icepool.Die[bool]':
        return compare(self, other, icepool.evaluator.IsSubsetEvaluator)

    def __gt__(self: 'Evaluable[T_co]', other: 'Evaluable[T_co]',
               /) -> 'icepool.Die[bool]':
        try:
            return compare(self, other,
                           icepool.evaluator.IsProperSupersetEvaluator)
        except TypeError:
            return NotImplemented

    def __ge__(self: 'Evaluable[T_co]', other: 'Evaluable[T_co]',
               /) -> 'icepool.Die[bool]':
        try:
            return compare(self, other, icepool.evaluator.IsSupersetEvaluator)
        except TypeError:
            return NotImplemented

    # The result has no truth value.
    def __eq__(  # type: ignore
            self: 'Evaluable[T_co]', other: 'Evaluable[T_co]',
            /) -> 'icepool.Die[bool]':
        try:
            return compare(self, other, icepool.evaluator.IsEqualSetEvaluator)
        except TypeError:
            return NotImplemented

    # The result has no truth value.
    def __ne__(  # type: ignore
            self: 'Evaluable[T_co]', other: 'Evaluable[T_co]',
            /) -> 'icepool.Die[bool]':
        try:
            return compare(self, other,
                           icepool.evaluator.IsNotEqualSetEvaluator)
        except TypeError:
            return NotImplemented

    def issuperset(self: 'Evaluable[T_co]', other: 'Evaluable[T_co]',
                   /) -> 'icepool.Die[bool]':
        return compare(self, other, icepool.evaluator.IsSupersetEvaluator)

    def isdisjoint(self: 'Evaluable[T_co]', other: 'Evaluable[T_co]',
                   /) -> 'icepool.Die[bool]':
        return compare(self, other, icepool.evaluator.IsDisjointSetEvaluator)


def evaluable_to_expression(
    evaluable: 'Evaluable[T]',) -> 'icepool.expression.MultisetExpression':
    """Converts a single argument to an evaluable."""
    if isinstance(evaluable, icepool.expression.FullyBoundExpression):
        return evaluable.expression
    elif isinstance(evaluable, (icepool.MultisetGenerator, Mapping, Sequence)):
        generator = icepool.implicit_convert_to_generator(evaluable)
        return icepool.expression.BoundGeneratorExpression(generator)
    else:
        raise TypeError(
            f'Could not convert argument of type {type(evaluable)}.')


def adjust_counts(
    left: 'Evaluable[T]', constant: int,
    operation_class: 'Type[icepool.expression.AdjustCountsExpression]'
) -> 'FullyBoundExpression[T]':
    left_expression = evaluable_to_expression(left)
    expression = operation_class(left_expression, constant)
    return icepool.expression.FullyBoundExpression(expression)


def binary_operation(
    left: 'Evaluable[T]', right: 'Evaluable[T]',
    operation_class: 'Type[icepool.expression.BinaryOperatorExpression]'
) -> 'FullyBoundExpression[T]':
    left_expression = evaluable_to_expression(left)
    right_expression = evaluable_to_expression(right)
    expression = operation_class(left_expression, right_expression)
    return icepool.expression.FullyBoundExpression(expression)


def compare(
    left: 'Evaluable[T]', right: 'Evaluable[T]',
    operation_class: Type['icepool.evaluator.ComparisonEvaluator']
) -> 'icepool.Die[bool]':
    left_expression = evaluable_to_expression(left)
    right_expression = evaluable_to_expression(right)
    evaluator = icepool.expression.ExpressionEvaluator(
        left_expression, right_expression, evaluator=operation_class())
    return evaluator.evaluate()
