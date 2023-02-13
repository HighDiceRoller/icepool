__docformat__ = 'google'

from types import EllipsisType
import icepool
import icepool.evaluator

import operator

from abc import ABC, abstractmethod
from functools import cached_property, reduce

from icepool.typing import T, U, Order, Outcome, T_contra
from typing import Any, Callable, Collection, Generic, Hashable, Mapping, Sequence, Type, overload


def implicit_convert_to_expression(
    arg:
    'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
) -> 'MultisetExpression[T_contra]':
    """Implcitly converts the argument to a `MultisetExpression`.

    Args:
        arg: The argument must either already be a `MultisetGenerator`;
            or a `Mapping` or `Collection`.
    """
    if isinstance(arg, MultisetExpression):
        return arg
    elif isinstance(arg, (Mapping, Sequence)):
        return icepool.Pool(arg)
    else:
        raise TypeError(
            f'Argument of type {arg.__class__.__name__} cannot be implicitly converted to a MultisetGenerator.'
        )


class MultisetExpression(ABC, Generic[T_contra]):
    """Abstract base class representing an expression that operates on multisets.

    Expression methods can be applied to `MultisetGenerator`s to do simple
    evaluations. For joint evaluations, try `multiset_function`.

    Use the provided operators and methods to build up more complicated
    expressions, or to attach a final evaluator.
    """

    @abstractmethod
    def _next_state(self, state, outcome: T_contra,
                    *counts: int) -> tuple[Hashable, int]:
        """Updates the state for this expression and does any necessary count modification.

        Args:
            state: The overall state. This will contain all information needed
                by this expression and any previous expressions.
            outcome: The current outcome.
            counts: The raw counts: first, the counts resulting from bound
                generators, then the counts from free variables.
                This must be passed to any previous expressions.

        Returns:
            * state: The updated state, which will be seen again by this
            `next_state` later.
            * count: The resulting count, which will be sent forward.
        """

    @abstractmethod
    def _order(self) -> Order:
        """Any ordering that is required by this expression.

        This should check any previous expressions for their order, and
        raise a ValueError for any incompatibilities.

        Returns:
            The required order.
        """

    @abstractmethod
    def _free_arity(self) -> int:
        """The minimum number of multisets/counts that must be provided to this expression.

        Any excess multisets/counts that are provided will be ignored.

        This does not include bound generators.
        """

    @abstractmethod
    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        """Returns a sequence of bound generators."""

    @abstractmethod
    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        """Replaces bound generators within this expression with free variables.

        Bound generators are replaced with free variables with index equal to
        their position in _bound_generators().

        Variables that are already free have their indexes shifted by the
        number of bound genrators.

        Args:
            prefix_start: The index of the next bound generator.
            free_start: The total number of bound generators.

        Returns:
            The transformed expression and the new prefix_start.
        """

    @staticmethod
    def _validate_output_arity(inner: 'MultisetExpression') -> None:
        """Validates that if the given expression is a generator, its output arity is 1."""
        if isinstance(inner,
                      icepool.MultisetGenerator) and inner.output_arity() != 1:
            raise ValueError(
                'Only generators with output arity of 1 may be bound to expressions. Use a multiset_function to select individual outputs.'
            )

    # Binary operators.

    def __add__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(self, other)

    def __radd__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(other, self)

    def disjoint_union(
        *args:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'MultisetExpression[T_contra]':
        """The combined elements from all of the multisets.

        Same as `a + b + c + ...`.

        Any resulting counts that would be negative are set to zero.

        Example:
        ```
        [1, 2, 2, 3] + [1, 2, 4] -> [1, 1, 2, 2, 2, 3, 4]
        ```
        """
        expressions = tuple(implicit_convert_to_expression(arg) for arg in args)
        return icepool.expression.DisjointUnionExpression(*expressions)

    def __sub__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.DifferenceExpression(self, other)

    def __rsub__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.DifferenceExpression(other, self)

    def difference(
        *args:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'MultisetExpression[T_contra]':
        """The elements from the left multiset that are not in any of the others.

        Same as `a - b - c - ...`.

        Any resulting counts that would be negative are set to zero.

        Example:
        ```
        [1, 2, 2, 3] - [1, 2, 4] -> [2, 3]
        ```

        If no arguments are given, the result will be an empty multiset, i.e.
        all zero counts.

        Note that, as a multiset operation, this will only cancel elements 1:1.
        If you want to drop all elements in a set of outcomes regardless of
        count, either use `drop_outcomes()` instead, or use a large number of
        counts on the right side.
        """
        expressions = tuple(implicit_convert_to_expression(arg) for arg in args)
        return icepool.expression.DifferenceExpression(*expressions)

    def __and__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.IntersectionExpression(self, other)

    def __rand__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.IntersectionExpression(other, self)

    def intersection(
        *args:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'MultisetExpression[T_contra]':
        """The elements that all the multisets have in common.

        Same as `a & b & c & ...`.

        Any resulting counts that would be negative are set to zero.

        Example:
        ```
        [1, 2, 2, 3] & [1, 2, 4] -> [1, 2]
        ```

        Note that, as a multiset operation, this will only intersect elements
        1:1.
        If you want to keep all elements in a set of outcomes regardless of
        count, either use `keep_outcomes()` instead, or use a large number of
        counts on the right side.
        """
        expressions = tuple(implicit_convert_to_expression(arg) for arg in args)
        return icepool.expression.IntersectionExpression(*expressions)

    def __or__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.UnionExpression(self, other)

    def __ror__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.UnionExpression(other, self)

    def union(
        *args:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'MultisetExpression[T_contra]':
        """The most of each outcome that appear in any of the multisets.

        Same as `a | b | c | ...`.

        Any resulting counts that would be negative are set to zero.

        Example:
        ```
        [1, 2, 2, 3] | [1, 2, 4] -> [1, 2, 2, 3, 4]
        ```
        """
        expressions = tuple(implicit_convert_to_expression(arg) for arg in args)
        return icepool.expression.UnionExpression(*expressions)

    def __xor__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(self, other)

    def __rxor__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except TypeError:
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(other, self)

    def symmetric_difference(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        """The elements that appear in the left or right multiset but not both.

        Same as `a ^ b`.

        Any negative counts are treated as zero.

        Example:
        ```
        [1, 2, 2, 3] ^ [1, 2, 4] -> [2, 3, 4]
        ```
        """
        other = implicit_convert_to_expression(other)
        return icepool.expression.SymmetricDifferenceExpression(self, other)

    def keep_outcomes(self,
                      target: Callable[[T_contra], bool] | Collection[T_contra],
                      /) -> 'MultisetExpression[T_contra]':
        """Keeps the elements in the target set of outcomes, and drops the rest by setting their counts to zero.

        This is similar to `intersection()`, except the right side is considered
        to have unlimited multiplicity.

        Args:
            target: A callable returning `True` iff the outcome should be kept,
                or a collection of outcomes to keep.
        """
        return icepool.expression.FilterOutcomesExpression(self, target)

    def drop_outcomes(self,
                      target: Callable[[T_contra], bool] | Collection[T_contra],
                      /) -> 'MultisetExpression[T_contra]':
        """Drops the elements in the target set of outcomes by setting their counts to zero, and keeps the rest.

        This is similar to `difference()`, except the right side is considered
        to have unlimited multiplicity.

        Args:
            target: A callable returning `True` iff the outcome should be
                dropped, or a collection of outcomes to drop.
        """
        return icepool.expression.FilterOutcomesExpression(self,
                                                           target,
                                                           invert=True)

    # Adjust counts.

    @overload
    def map_counts(self, func: Callable[[int], int],
                   /) -> 'MultisetExpression[T_contra]':
        ...

    @overload
    def map_counts(self, func: Callable[[T_contra, int], int],
                   /) -> 'MultisetExpression[T_contra]':
        ...

    def map_counts(self,
                   func: Callable[[int], int] | Callable[[T_contra, int], int],
                   /) -> 'MultisetExpression[T_contra]':
        """Maps the counts to new counts.

        Args:
            func: A function that takes `count` or `outcome, count` and produces
                a modified count.
        """
        return icepool.expression.MapCountsExpression(self, func)

    def __mul__(self, other: int) -> 'MultisetExpression[T_contra]':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, other)

    # Commutable in this case.
    def __rmul__(self, other: int) -> 'MultisetExpression[T_contra]':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, other)

    def multiply_counts(self, constant: int,
                        /) -> 'MultisetExpression[T_contra]':
        """Multiplies all counts by a constant.

        Same as `self * constant`.

        Example:
        ```
        Pool([1, 2, 2, 3]) * 2 -> [1, 1, 2, 2, 2, 2, 3, 3]
        ```
        """
        return self * constant

    def __floordiv__(self, other: int) -> 'MultisetExpression[T_contra]':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.FloorDivCountsExpression(self, other)

    def divide_counts(self, constant: int, /) -> 'MultisetExpression[T_contra]':
        """Divides all counts by a constant (rounding down).

        Same as `self // constant`.

        Example:
        ```
        Pool([1, 2, 2, 3]) // 2 -> [2]
        ```
        """
        return self // constant

    def filter_counts(self, min_count: int) -> 'MultisetExpression[T_contra]':
        """Counts less than `min_count` are treated as zero.

        For example, `generator.filter_counts(2)` would only produce
        pairs and better.

        Example:
        ```
        Pool([1, 2, 2, 3]).filter_counts(2) -> [2, 2]
        ```
        """
        return icepool.expression.FilterCountsExpression(self, min_count)

    def unique(self, max_count: int = 1) -> 'MultisetExpression[T_contra]':
        """Counts each outcome at most `max_count` times.

        For example, `generator.unique(2)` would count each outcome at most
        twice.

        Example:
        ```
        Pool([1, 2, 2, 3]).unique() -> [1, 2, 3]
        ```
        """
        return icepool.expression.UniqueExpression(self, max_count)

    # Keep highest / lowest.

    @overload
    def keep(
        self, index: slice | Sequence[int | EllipsisType]
    ) -> 'MultisetExpression[T_contra]':
        ...

    @overload
    def keep(
        self, index: int
    ) -> 'icepool.Die[T_contra] | icepool.MultisetEvaluator[T_contra, T_contra]':
        ...

    def keep(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'MultisetExpression[T_contra] | icepool.Die[T_contra] | icepool.MultisetEvaluator[T_contra, T_contra]':
        """Selects pulls after drawing and sorting.

        This is less capable and less efficient than the `Pool` version.
        In particular, it does not know how many elements it is selecting from,
        so it must be anchored at either the lowest or highest end. On the other
        hand, this can be applied to any expression.

        The valid types of argument are:

        * A `slice`. If both start and stop are provided, they must both be
            non-negative or both be negative. step is not supported.
        * A sequence of `int` with `...` (`Ellipsis`) at exactly one end.
            Each sorted element will be counted that many times, with the
            `Ellipsis` treated as enough zeros (possibly "negative") to
            fill the rest of the elements.
        * An `int`, which evaluates by taking the element at the specified
            index. In this case the result is a `Die` (if fully bound) or a
            `MultisetEvaluator` (if there are free variables).

        Use the `[]` operator for the same effect as this method.
        """
        if isinstance(index, int):
            return self.evaluate(
                evaluator=icepool.evaluator.KeepEvaluator(index))
        else:
            return icepool.expression.KeepExpression(self, index)

    @overload
    def __getitem__(
        self, index: slice | Sequence[int | EllipsisType]
    ) -> 'MultisetExpression[T_contra]':
        ...

    @overload
    def __getitem__(
        self, index: int
    ) -> 'icepool.Die[T_contra] | icepool.MultisetEvaluator[T_contra, T_contra]':
        ...

    def __getitem__(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'MultisetExpression[T_contra] | icepool.Die[T_contra] | icepool.MultisetEvaluator[T_contra, T_contra]':
        return self.keep(index)

    def lowest(self,
               keep: int = 1,
               drop: int = 0) -> 'MultisetExpression[T_contra]':
        """Keep some of the lowest elements from this multiset and drop the rest.

        In contrast to the die and free function versions, this does not
        automatically sum the dice. Use `.sum()` afterwards if you want to sum.
        Alternatively, you can perform some other evaluation.

        Args:
            keep: The number of lowest elements will be kept.
            drop: This number of lowest elements will be dropped before keeping.
        """
        t = (0,) * drop + (1,) * keep + (...,)
        return self.keep(t)

    def highest(self,
                keep: int = 1,
                drop: int = 0) -> 'MultisetExpression[T_contra]':
        """Keep some of the highest elements from this multiset and drop the rest.

        In contrast to the die and free function versions, this does not
        automatically sum the dice. Use `.sum()` afterwards if you want to sum.
        Alternatively, you can perform some other evaluation.

        Args:
            keep: The number of highest elements will be kept.
            drop: This number of highest elements will be dropped before keeping.
        """
        t = (...,) + (1,) * keep + (0,) * drop
        return self.keep(t)

    # Evaluations.

    def evaluate(
        *expressions: 'MultisetExpression[T_contra]',
        evaluator: 'icepool.MultisetEvaluator[T_contra, U]'
    ) -> 'icepool.Die[U] | icepool.MultisetEvaluator[T_contra, U]':
        """Attaches a final `MultisetEvaluator` to expressions.

        All of the `MultisetExpression` methods following this are evaluations.

        Returns:
            A `Die` if all expressions are fully bound.
            A `MultisetEvaluator` otherwise.
        """
        if all(
                isinstance(expression, icepool.MultisetGenerator)
                for expression in expressions):
            return evaluator.evaluate(*expressions)
        evaluator = icepool.evaluator.ExpressionEvaluator(*expressions,
                                                          evaluator=evaluator)
        if evaluator._free_arity == 0:
            return evaluator.evaluate()
        else:
            return evaluator

    def expand(
        self
    ) -> 'icepool.Die[tuple[T_contra, ...]] | icepool.MultisetEvaluator[T_contra, tuple[T_contra, ...]]':
        """All elements of the multiset.

        This is expensive and not recommended unless there are few possibilities.
        """
        return self.evaluate(evaluator=icepool.evaluator.ExpandEvaluator())

    def sum(
        self,
        map: Callable[[T_contra], U] | Mapping[T_contra, U] | None = None
    ) -> 'icepool.Die[U] | icepool.MultisetEvaluator[T_contra, U]':
        """The sum of all elements."""
        if map is None:
            return self.evaluate(evaluator=icepool.evaluator.sum_evaluator)
        else:
            return self.evaluate(evaluator=icepool.evaluator.SumEvaluator(map))

    def count(
            self
    ) -> 'icepool.Die[int] | icepool.MultisetEvaluator[T_contra, int]':
        """The total number of elements in the multiset.

        This is usually not very interesting unless some other operation is
        performed first. Examples:

        `generator.unique().count()` will count the number of unique outcomes.

        `(generator & [4, 5, 6]).count()` will count up to one each of
        4, 5, and 6.
        """
        return self.evaluate(evaluator=icepool.evaluator.count_evaluator)

    def any(
        self
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        """Whether the multiset has at least one positive count."""
        return self.evaluate(evaluator=icepool.evaluator.any_evaluator)

    def highest_outcome_and_count(
        self
    ) -> 'icepool.Die[tuple[T_contra, int]] | icepool.MultisetEvaluator[T_contra, tuple[T_contra, int]]':
        """The highest outcome with positive count, along with that count.

        If no outcomes have positive count, an arbitrary outcome will be
        produced with a 0 count.
        """
        return self.evaluate(
            evaluator=icepool.evaluator.HighestOutcomeAndCountEvaluator())

    def all_counts(
        self,
        filter: int | None = 1
    ) -> 'icepool.Die[tuple[int, ...]] | icepool.MultisetEvaluator[T_contra, tuple[int, ...]]':
        """Produces a tuple of all counts, i.e. the sizes of all matching sets.

        Args:
            filter: Any counts below this value will not be in the output.
                For example, `filter=2` will only produce pairs and better.
                If `None`, no filtering will be done.

                Why not just place `filter_counts()` before this?
                `filter_counts()` operates by setting counts to zero, so you
                would still need an argument to specify whether you want to
                output zero counts. So we might as well use the argument to do
                both.
        """
        return self.evaluate(evaluator=icepool.evaluator.AllCountsEvaluator(
            filter=filter))

    def largest_count(
            self
    ) -> 'icepool.Die[int] | icepool.MultisetEvaluator[T_contra, int]':
        """The size of the largest matching set among the elements."""
        return self.evaluate(
            evaluator=icepool.evaluator.LargestCountEvaluator())

    def largest_count_and_outcome(
        self
    ) -> 'icepool.Die[tuple[int, T_contra]] | icepool.MultisetEvaluator[T_contra, tuple[int, T_contra]]':
        """The largest matching set among the elements and the corresponding outcome."""
        return self.evaluate(
            evaluator=icepool.evaluator.LargestCountAndOutcomeEvaluator())

    def largest_straight(
        self: 'MultisetExpression[int]'
    ) -> 'icepool.Die[int] | icepool.MultisetEvaluator[int, int]':
        """The size of the largest straight among the elements.

        Outcomes must be `int`s.
        """
        return self.evaluate(
            evaluator=icepool.evaluator.LargestStraightEvaluator())

    def largest_straight_and_outcome(
        self: 'MultisetExpression[int]'
    ) -> 'icepool.Die[tuple[int, int]] | icepool.MultisetEvaluator[int, tuple[int, int]]':
        """The size of the largest straight among the elements and the highest outcome in that straight.

        Outcomes must be `int`s.
        """
        return self.evaluate(
            evaluator=icepool.evaluator.LargestStraightAndOutcomeEvaluator())

    # Comparators.

    def _compare(
        self, right:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
        operation_class: Type['icepool.evaluator.ComparisonEvaluator']
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        if isinstance(right, MultisetExpression):
            evaluator = icepool.evaluator.ExpressionEvaluator(
                self, right, evaluator=operation_class())
        elif isinstance(right, (Mapping, Sequence)):
            right_expression = icepool.implicit_convert_to_expression(right)
            evaluator = icepool.evaluator.ExpressionEvaluator(
                self, right_expression, evaluator=operation_class())
        else:
            raise TypeError('Right side is not comparable.')

        if evaluator._free_arity == 0:
            return evaluator.evaluate()
        else:
            return evaluator

    def __lt__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        try:
            return self._compare(other,
                                 icepool.evaluator.IsProperSubsetEvaluator)
        except TypeError:
            return NotImplemented

    def __le__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        try:
            return self._compare(other, icepool.evaluator.IsSubsetEvaluator)
        except TypeError:
            return NotImplemented

    def issubset(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        """Whether this multiset is a subset of the other multiset.

        Same as `self <= other`.
        """
        return self._compare(other, icepool.evaluator.IsSubsetEvaluator)

    def __gt__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        try:
            return self._compare(other,
                                 icepool.evaluator.IsProperSupersetEvaluator)
        except TypeError:
            return NotImplemented

    def __ge__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        try:
            return self._compare(other, icepool.evaluator.IsSupersetEvaluator)
        except TypeError:
            return NotImplemented

    def issuperset(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        """Whether this multiset is a superset of the other multiset.

        Same as `self >= other`.
        """
        return self._compare(other, icepool.evaluator.IsSupersetEvaluator)

    # The result has no truth value.
    def __eq__(  # type: ignore
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        try:
            return self._compare(other, icepool.evaluator.IsEqualSetEvaluator)
        except TypeError:
            return NotImplemented

    # The result has no truth value.
    def __ne__(  # type: ignore
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        try:
            return self._compare(other,
                                 icepool.evaluator.IsNotEqualSetEvaluator)
        except TypeError:
            return NotImplemented

    def isdisjoint(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /
    ) -> 'icepool.Die[bool] | icepool.MultisetEvaluator[T_contra, bool]':
        """Whether this multiset is disjoint from the other multiset."""
        return self._compare(other, icepool.evaluator.IsDisjointSetEvaluator)
