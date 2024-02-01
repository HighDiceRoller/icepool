__docformat__ = 'google'

from types import EllipsisType
import icepool
import icepool.evaluator

import operator

from abc import ABC, abstractmethod

from icepool.typing import T, U, ImplicitConversionError, Order, Outcome, T_contra
from typing import Any, Callable, Collection, Generic, Hashable, Literal, Mapping, Sequence, Type, overload


def implicit_convert_to_expression(
    arg:
    'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
) -> 'MultisetExpression[T_contra]':
    """Implcitly converts the argument to a `MultisetExpression`.

    Args:
        arg: The argument must either already be a `MultisetExpression`;
            or a `Mapping` or `Collection`.
    """
    if isinstance(arg, MultisetExpression):
        return arg
    elif isinstance(arg, (Mapping, Sequence)):
        return icepool.Pool(arg)
    else:
        raise ImplicitConversionError(
            f'Argument of type {arg.__class__.__name__} cannot be implicitly converted to a Pool.'
        )


class MultisetExpression(ABC, Generic[T_contra]):
    """Abstract base class representing an expression that operates on multisets.

    Expression methods can be applied to `MultisetGenerator`s to do simple
    evaluations. For joint evaluations, try `multiset_function`.

    Use the provided operations to build up more complicated
    expressions, or to attach a final evaluator.

    Operations include:

    | Operation                   | Count / notes                      |
    |:----------------------------|:-----------------------------------|
    | `additive_union`, `+`       | `l + r`                            |
    | `difference`, `-`           | `l - r`                            |
    | `intersection`, `&`         | `min(l, r)`                        |
    | `union`, `\\|`               | `max(l, r)`                        |
    | `symmetric_difference`, `^` | `abs(l - r)`                       |
    | `multiply_counts`, `*`      | `count * n`                        |
    | `divide_counts`, `//`       | `count // n`                       |
    | `modulo_counts`, `%`        | `count % n`                        |
    | `keep_counts_ge` etc.       | `count if count >= n else 0` etc.  |
    | unary `+`                   | same as `keep_counts_ge(0)`        |
    | unary `-`                   | reverses the sign of all counts    |
    | `unique`                    | `min(count, n)`                    |
    | `keep_outcomes`             | `count if outcome in t else 0`     |
    | `drop_outcomes`             | `count if outcome not in t else 0` |
    | `map_counts`                | `f(outcome, *counts)`              |
    | `keep`, `[]`                | less capable than `Pool` version   |
    | `highest`                   | less capable than `Pool` version   |
    | `lowest`                    | less capable than `Pool` version   |

    | Evaluator                      | Summary                                                                    |
    |:-------------------------------|:---------------------------------------------------------------------------|
    | `issubset`, `<=`               | Whether the left side's counts are all <= their counterparts on the right  |
    | `issuperset`, `>=`             | Whether the left side's counts are all >= their counterparts on the right  |
    | `isdisjoint`                   | Whether the left side has no positive counts in common with the right side |
    | `<`                            | As `<=`, but `False` if the two multisets are equal                        |
    | `>`                            | As `>=`, but `False` if the two multisets are equal                        |
    | `==`                           | Whether the left side has all the same counts as the right side            |
    | `!=`                           | Whether the left side has any different counts to the right side           |
    | `expand`                       | All elements in ascending order                                            |
    | `sum`                          | Sum of all elements                                                        |
    | `count`                        | The number of elements                                                     |
    | `any`                          | Whether there is at least 1 element                                        |
    | `highest_outcome_and_count`    | The highest outcome and how many of that outcome                           |
    | `all_counts`                   | All counts in descending order                                             |
    | `largest_count`                | The single largest count, aka x-of-a-kind                                  |
    | `largest_count_and_outcome`    | Same but also with the corresponding outcome                               |
    | `count_subset`, `//`           | The number of times the right side is contained in the left side           |
    | `largest_straight`             | Length of longest consecutive sequence                                     |
    | `largest_straight_and_outcome` | Same but also with the corresponding outcome                               |
    | `all_straights`                | Lengths of all consecutive sequences in descending order                   |
    """

    @abstractmethod
    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:
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
                'Only generators with output arity of 1 may be bound to expressions.\nUse a multiset_function to select individual outputs.'
            )

    # Binary operators.

    def __add__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(self, other)

    def __radd__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(other, self)

    def additive_union(
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
        expressions = tuple(
            implicit_convert_to_expression(arg) for arg in args)
        return icepool.expression.DisjointUnionExpression(*expressions)

    def __sub__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
            return NotImplemented
        return icepool.expression.DifferenceExpression(self, other)

    def __rsub__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
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
        expressions = tuple(
            implicit_convert_to_expression(arg) for arg in args)
        return icepool.expression.DifferenceExpression(*expressions)

    def __and__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
            return NotImplemented
        return icepool.expression.IntersectionExpression(self, other)

    def __rand__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
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
        expressions = tuple(
            implicit_convert_to_expression(arg) for arg in args)
        return icepool.expression.IntersectionExpression(*expressions)

    def __or__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
            return NotImplemented
        return icepool.expression.UnionExpression(self, other)

    def __ror__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
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
        expressions = tuple(
            implicit_convert_to_expression(arg) for arg in args)
        return icepool.expression.UnionExpression(*expressions)

    def __xor__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(self, other)

    def __rxor__(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        try:
            other = implicit_convert_to_expression(other)
        except ImplicitConversionError:
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(other, self)

    def symmetric_difference(
            self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        """The elements that appear in the left or right multiset but not both.

        Same as `a ^ b`.

        Specifically, this produces the absolute difference between counts.
        If you don't want negative counts to be used from the inputs, you can
        do `left.keep_counts_ge(0) ^ right.keep_counts_ge(0)`.

        Example:
        ```
        [1, 2, 2, 3] ^ [1, 2, 4] -> [2, 3, 4]
        ```
        """
        other = implicit_convert_to_expression(other)
        return icepool.expression.SymmetricDifferenceExpression(self, other)

    def keep_outcomes(
            self, target:
        'Callable[[T_contra], bool] | Collection[T_contra] | MultisetExpression[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        """Keeps the elements in the target set of outcomes, and drops the rest by setting their counts to zero.

        This is similar to `intersection()`, except the right side is considered
        to have unlimited multiplicity.

        Args:
            target: A callable returning `True` iff the outcome should be kept,
                or an expression or collection of outcomes to keep.
        """
        if isinstance(target, MultisetExpression):
            return icepool.expression.FilterOutcomesBinaryExpression(
                self, target)
        else:
            return icepool.expression.FilterOutcomesExpression(self, target)

    def drop_outcomes(
            self, target:
        'Callable[[T_contra], bool] | Collection[T_contra] | MultisetExpression[T_contra]',
            /) -> 'MultisetExpression[T_contra]':
        """Drops the elements in the target set of outcomes by setting their counts to zero, and keeps the rest.

        This is similar to `difference()`, except the right side is considered
        to have unlimited multiplicity.

        Args:
            target: A callable returning `True` iff the outcome should be
                dropped, or an expression or collection of outcomes to drop.
        """
        if isinstance(target, MultisetExpression):
            return icepool.expression.FilterOutcomesBinaryExpression(
                self, target, invert=True)
        else:
            return icepool.expression.FilterOutcomesExpression(self,
                                                               target,
                                                               invert=True)

    # Adjust counts.

    def map_counts(
        *args:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
        function: Callable[[int], int] | Callable[[T_contra, int], int]
    ) -> 'MultisetExpression[T_contra]':
        """Maps the counts to new counts.

        Args:
            function: A function that takes `outcome, *counts` and produces a
                combined count.
        """
        expressions = tuple(
            implicit_convert_to_expression(arg) for arg in args)
        return icepool.expression.MapCountsExpression(*expressions,
                                                      function=function)

    def __mul__(self, n: int) -> 'MultisetExpression[T_contra]':
        if not isinstance(n, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, n)

    # Commutable in this case.
    def __rmul__(self, n: int) -> 'MultisetExpression[T_contra]':
        if not isinstance(n, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, n)

    def multiply_counts(self, n: int, /) -> 'MultisetExpression[T_contra]':
        """Multiplies all counts by n.

        Same as `self * n`.

        Example:
        ```
        Pool([1, 2, 2, 3]) * 2 -> [1, 1, 2, 2, 2, 2, 3, 3]
        ```
        """
        return self * n

    @overload
    def __floordiv__(self, other: int) -> 'MultisetExpression[T_contra]':
        ...

    @overload
    def __floordiv__(
        self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'icepool.Die[int] | icepool.MultisetEvaluator[T_contra, int]':
        """Same as divide_counts()."""

    @overload
    def __floordiv__(
        self, other:
        'int | MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'MultisetExpression[T_contra] | icepool.Die[int] | icepool.MultisetEvaluator[T_contra, int]':
        """Same as count_subset()."""

    def __floordiv__(
        self, other:
        'int | MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'MultisetExpression[T_contra] | icepool.Die[int] | icepool.MultisetEvaluator[T_contra, int]':
        if isinstance(other, int):
            return self.divide_counts(other)
        else:
            return self.count_subset(other)

    def divide_counts(self, n: int, /) -> 'MultisetExpression[T_contra]':
        """Divides all counts by n (rounding down).

        Same as `self // n`.

        Example:
        ```
        Pool([1, 2, 2, 3]) // 2 -> [2]
        ```
        """
        return icepool.expression.FloorDivCountsExpression(self, n)

    def __mod__(self, n: int, /) -> 'MultisetExpression[T_contra]':
        if not isinstance(n, int):
            return NotImplemented
        return icepool.expression.ModuloCountsExpression(self, n)

    def modulo_counts(self, n: int, /) -> 'MultisetExpression[T_contra]':
        """Moduos all counts by n.

        Same as `self % n`.

        Example:
        ```
        Pool([1, 2, 2, 3]) % 2 -> [1, 3]
        ```
        """
        return self % n

    def __pos__(self) -> 'MultisetExpression[T_contra]':
        return icepool.expression.KeepCountsExpression(self, 0, operator.ge)

    def __neg__(self) -> 'MultisetExpression[T_contra]':
        return icepool.expression.MultiplyCountsExpression(self, -1)

    def keep_counts_le(self, n: int, /) -> 'MultisetExpression[T_contra]':
        """Keeps counts that are <= n, treating the rest as zero.

        For example, `expression.keep_counts_le(2)` would remove triplets and
        better.

        Example:
        ```
        Pool([1, 2, 2, 3, 3, 3]).keep_counts_le(2) -> [1, 2, 2]
        ```
        """
        return icepool.expression.KeepCountsExpression(self, n, operator.le)

    def keep_counts_lt(self, n: int, /) -> 'MultisetExpression[T_contra]':
        """Keeps counts that are < n, treating the rest as zero.

        For example, `expression.keep_counts_lt(2)` would remove doubles,
        triplets...

        Example:
        ```
        Pool([1, 2, 2, 3, 3, 3]).keep_counts_lt(2) -> [1]
        ```
        """
        return icepool.expression.KeepCountsExpression(self, n, operator.lt)

    def keep_counts_ge(self, n: int, /) -> 'MultisetExpression[T_contra]':
        """Keeps counts that are >= n, treating the rest as zero.

        For example, `expression.keep_counts_ge(2)` would only produce
        pairs and better.
        
        `expression.keep_countss_ge(0)` is useful for removing negative counts. 
        You can use the unary operator `+expression` for the same effect.

        Example:
        ```
        Pool([1, 2, 2, 3, 3, 3]).keep_counts_ge(2) -> [2, 2, 3, 3, 3]
        ```
        """
        return icepool.expression.KeepCountsExpression(self, n, operator.ge)

    def keep_counts_gt(self, n: int, /) -> 'MultisetExpression[T_contra]':
        """Keeps counts that are < n, treating the rest as zero.

        For example, `expression.keep_counts_gt(2)` would remove singles and
        doubles.

        Example:
        ```
        Pool([1, 2, 2, 3, 3, 3]).keep_counts_gt(2) -> [3, 3, 3]
        ```
        """
        return icepool.expression.KeepCountsExpression(self, n, operator.gt)

    def keep_counts_eq(self, n: int, /) -> 'MultisetExpression[T_contra]':
        """Keeps counts that are == n, treating the rest as zero.

        For example, `expression.keep_counts_eq(2)` would keep pairs but not
        singles or triplets.

        Example:
        ```
        Pool([1, 2, 2, 3, 3, 3]).keep_counts_le(2) -> [2, 2]
        ```
        """
        return icepool.expression.KeepCountsExpression(self, n, operator.eq)

    def keep_counts_ne(self, n: int, /) -> 'MultisetExpression[T_contra]':
        """Keeps counts that are != n, treating the rest as zero.

        For example, `expression.keep_counts_eq(2)` would drop pairs but keep
        singles and triplets.

        Example:
        ```
        Pool([1, 2, 2, 3, 3, 3]).keep_counts_ne(2) -> [1, 3, 3, 3]
        ```
        """
        return icepool.expression.KeepCountsExpression(self, n, operator.ne)

    def unique(self, n: int = 1, /) -> 'MultisetExpression[T_contra]':
        """Counts each outcome at most `n` times.

        For example, `generator.unique(2)` would count each outcome at most
        twice.

        Example:
        ```
        Pool([1, 2, 2, 3]).unique() -> [1, 2, 3]
        ```
        """
        return icepool.expression.UniqueExpression(self, n)

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
        so it must be anchored at the starting end. The advantage is that it
        can be applied to any expression.

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

        This requires the outcomes to be evaluated in ascending order.

        Args:
            keep: The number of lowest elements will be kept.
            drop: This number of lowest elements will be dropped before keeping.
        """
        t = (0, ) * drop + (1, ) * keep + (..., )
        return self.keep(t)

    def highest(self,
                keep: int = 1,
                drop: int = 0) -> 'MultisetExpression[T_contra]':
        """Keep some of the highest elements from this multiset and drop the rest.

        In contrast to the die and free function versions, this does not
        automatically sum the dice. Use `.sum()` afterwards if you want to sum.
        Alternatively, you can perform some other evaluation.

        This requires the outcomes to be evaluated in descending order.

        Args:
            keep: The number of highest elements will be kept.
            drop: This number of highest elements will be dropped before keeping.
        """
        t = (..., ) + (1, ) * keep + (0, ) * drop
        return self.keep(t)

    # Evaluations.

    def evaluate(
        *expressions: 'MultisetExpression[T_contra]',
        evaluator: 'icepool.MultisetEvaluator[T_contra, U]'
    ) -> 'icepool.Die[U] | icepool.MultisetEvaluator[T_contra, U]':
        """Attaches a final `MultisetEvaluator` to expressions.

        All of the `MultisetExpression` methods below are evaluations,
        as are the operators `<, <=, >, >=, !=, ==`. This means if the
        expression is fully bound, it will be evaluated to a `Die`.

        Returns:
            A `Die` if the expression is are fully bound.
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
        self,
        order: Order = Order.Ascending
    ) -> 'icepool.Die[tuple[T_contra, ...]] | icepool.MultisetEvaluator[T_contra, tuple[T_contra, ...]]':
        """Evaluation: All elements of the multiset in ascending order.

        This is expensive and not recommended unless there are few possibilities.

        Args:
            order: Whether the elements are in ascending (default) or descending
                order.
        """
        return self.evaluate(evaluator=icepool.evaluator.ExpandEvaluator(
            order=order))

    def sum(
        self,
        map: Callable[[T_contra], U] | Mapping[T_contra, U] | None = None
    ) -> 'icepool.Die[U] | icepool.MultisetEvaluator[T_contra, U]':
        """Evaluation: The sum of all elements."""
        if map is None:
            return self.evaluate(evaluator=icepool.evaluator.sum_evaluator)
        else:
            return self.evaluate(evaluator=icepool.evaluator.SumEvaluator(map))

    def count(
            self
    ) -> 'icepool.Die[int] | icepool.MultisetEvaluator[T_contra, int]':
        """Evaluation: The total number of elements in the multiset.

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
        """Evaluation: Whether the multiset has at least one positive count."""
        return self.evaluate(evaluator=icepool.evaluator.any_evaluator)

    def highest_outcome_and_count(
        self
    ) -> 'icepool.Die[tuple[T_contra, int]] | icepool.MultisetEvaluator[T_contra, tuple[T_contra, int]]':
        """Evaluation: The highest outcome with positive count, along with that count.

        If no outcomes have positive count, the min outcome will be returned with 0 count.
        """
        return self.evaluate(
            evaluator=icepool.evaluator.HighestOutcomeAndCountEvaluator())

    def all_counts(
        self,
        filter: int | None = 1
    ) -> 'icepool.Die[tuple[int, ...]] | icepool.MultisetEvaluator[T_contra, tuple[int, ...]]':
        """Evaluation: Sorted tuple of all counts, i.e. the sizes of all matching sets.

        The sizes are in **descending** order.

        Args:
            filter: Any counts below this value will not be in the output.
                For example, `filter=2` will only produce pairs and better.
                If `None`, no filtering will be done.

                Why not just place `keep_countss_ge()` before this?
                `keep_countss_ge()` operates by setting counts to zero, so you
                would still need an argument to specify whether you want to
                output zero counts. So we might as well use the argument to do
                both.
        """
        return self.evaluate(evaluator=icepool.evaluator.AllCountsEvaluator(
            filter=filter))

    def largest_count(
            self
    ) -> 'icepool.Die[int] | icepool.MultisetEvaluator[T_contra, int]':
        """Evaluation: The size of the largest matching set among the elements."""
        return self.evaluate(
            evaluator=icepool.evaluator.LargestCountEvaluator())

    def largest_count_and_outcome(
        self
    ) -> 'icepool.Die[tuple[int, T_contra]] | icepool.MultisetEvaluator[T_contra, tuple[int, T_contra]]':
        """Evaluation: The largest matching set among the elements and the corresponding outcome."""
        return self.evaluate(
            evaluator=icepool.evaluator.LargestCountAndOutcomeEvaluator())

    def __rfloordiv__(
        self, other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]'
    ) -> 'icepool.Die[int] | icepool.MultisetEvaluator[T_contra, int]':
        other = implicit_convert_to_expression(other)
        return other.count_subset(self)

    def count_subset(
        self,
        divisor:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
        /,
        *,
        empty_divisor: int | None = None
    ) -> 'icepool.Die[int] | icepool.MultisetEvaluator[T_contra, int]':
        """Evaluation: The number of times the divisor is contained in this multiset.
        
        Args:
            divisor: The multiset to divide by.
            empty_divisor: If the divisor is empty, the outcome will be this.
                If not set, `ZeroDivisionError` will be raised for an empty
                right side.

        Raises:
            ZeroDivisionError: If the divisor may be empty and 
                empty_divisor_outcome is not set.
        """
        divisor = implicit_convert_to_expression(divisor)
        return self.evaluate(divisor,
                             evaluator=icepool.evaluator.CountSubsetEvaluator(
                                 empty_divisor=empty_divisor))

    def largest_straight(
        self: 'MultisetExpression[int]'
    ) -> 'icepool.Die[int] | icepool.MultisetEvaluator[int, int]':
        """Evaluation: The size of the largest straight among the elements.

        Outcomes must be `int`s.
        """
        return self.evaluate(
            evaluator=icepool.evaluator.LargestStraightEvaluator())

    def largest_straight_and_outcome(
        self: 'MultisetExpression[int]'
    ) -> 'icepool.Die[tuple[int, int]] | icepool.MultisetEvaluator[int, tuple[int, int]]':
        """Evaluation: The size of the largest straight among the elements and the highest outcome in that straight.

        Outcomes must be `int`s.
        """
        return self.evaluate(
            evaluator=icepool.evaluator.LargestStraightAndOutcomeEvaluator())

    def all_straights(
        self: 'MultisetExpression[int]'
    ) -> 'icepool.Die[tuple[int, ...]] | icepool.MultisetEvaluator[int, tuple[int, ...]]':
        """Evaluation: The sizes of all straights.

        The sizes are in **descending** order.

        Each element can only contribute to one straight, though duplicates can
        produce overlapping straights.
        """
        return self.evaluate(
            evaluator=icepool.evaluator.AllStraightsEvaluator())

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
            raise TypeError('Operand not comparable with expression.')

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
        """Evaluation: Whether this multiset is a subset of the other multiset.

        Specifically, if this multiset has a lesser or equal count for each
        outcome than the other multiset, this evaluates to `True`; 
        if there is some outcome for which this multiset has a greater count 
        than the other multiset, this evaluates to `False`.

        `issubset` is the same as `self <= other`.
        
        `self < other` evaluates a proper subset relation, which is the same
        except the result is `False` if the two multisets are exactly equal.
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
        """Evaluation: Whether this multiset is a superset of the other multiset.

        Specifically, if this multiset has a greater or equal count for each
        outcome than the other multiset, this evaluates to `True`; 
        if there is some  outcome for which this multiset has a lesser count 
        than the other multiset, this evaluates to `False`.
        
        A typical use of this evaluation is testing for the presence of a
        combo of cards in a hand, e.g.

        ```
        deck.deal(5) >= ['a', 'a', 'b']
        ```

        represents the chance that a deal of 5 cards contains at least two 'a's
        and one 'b'.

        `issuperset` is the same as `self >= other`.

        `self > other` evaluates a proper superset relation, which is the same
        except the result is `False` if the two multisets are exactly equal.
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
        """Evaluation: Whether this multiset is disjoint from the other multiset.
        
        Specifically, this evaluates to `False` if there is any outcome for
        which both multisets have positive count, and `True` if there is not.
        """
        return self._compare(other, icepool.evaluator.IsDisjointSetEvaluator)

    def compair_lt(
            self,
            other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            *,
            order: Order = Order.Descending):
        """Evaluation: EXPERIMENTAL: Compare pairs of elements in sorted order, counting how many pairs `self` is < `other`.

        Any extra unpaired elements do not affect the result.

        Args:
            other: The other multiset to compare.
            order: Which order elements will be matched in.
                Default is descending.
        """
        other = implicit_convert_to_expression(other)
        return self.evaluate(other,
                             evaluator=icepool.evaluator.CompairEvalautor(
                                 order=order,
                                 tie=0,
                                 left_greater=0,
                                 right_greater=1))

    def compair_le(
            self,
            other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            *,
            order: Order = Order.Descending):
        """Evaluation: EXPERIMENTAL: Compare pairs of elements in sorted order, counting how many pairs `self` is <= `other`.

        Any extra unpaired elements do not affect the result.

        Example: number of armies destroyed by the defender in a 
        3v2 attack in *RISK*:
        ```
        d6.pool(3).compair_le(d6.pool(2))
        ```

        Args:
            other: The other multiset to compare.
            order: Which order elements will be matched in.
                Default is descending.
        """
        other = implicit_convert_to_expression(other)
        return self.evaluate(other,
                             evaluator=icepool.evaluator.CompairEvalautor(
                                 order=order,
                                 tie=1,
                                 left_greater=0,
                                 right_greater=1))

    def compair_gt(
            self,
            other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            *,
            order: Order = Order.Descending):
        """Evaluation: EXPERIMENTAL: Compare pairs of elements in sorted order, counting how many pairs `self` is > `other`.

        Any extra unpaired elements do not affect the result.

        Example: number of armies destroyed by the attacker in a 
        3v2 attack in *RISK*:
        ```
        d6.pool(3).compair_gt(d6.pool(2))
        ```

        Args:
            other: The other multiset to compare.
            order: Which order elements will be matched in.
                Default is descending.
        """
        other = implicit_convert_to_expression(other)
        return self.evaluate(other,
                             evaluator=icepool.evaluator.CompairEvalautor(
                                 order=order,
                                 tie=0,
                                 left_greater=1,
                                 right_greater=0))

    def compair_ge(
            self,
            other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            *,
            order: Order = Order.Descending):
        """Evaluation: EXPERIMENTAL: Compare pairs of elements in sorted order, counting how many pairs `self` is >= `other`.

        Any extra unpaired elements do not affect the result.

        Args:
            other: The other multiset to compare.
            order: Which order elements will be matched in.
                Default is descending.
        """
        other = implicit_convert_to_expression(other)
        return self.evaluate(other,
                             evaluator=icepool.evaluator.CompairEvalautor(
                                 order=order,
                                 tie=1,
                                 left_greater=1,
                                 right_greater=0))

    def compair_eq(
            self,
            other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            *,
            order: Order = Order.Descending):
        """Evaluation: EXPERIMENTAL: Compare pairs of elements in sorted order, counting how many pairs `self` is >= `other`.

        Any extra unpaired elements do not affect the result.

        Args:
            other: The other multiset to compare.
            order: Which order elements will be matched in.
                Default is descending.
        """
        other = implicit_convert_to_expression(other)
        return self.evaluate(other,
                             evaluator=icepool.evaluator.CompairEvalautor(
                                 order=order,
                                 tie=1,
                                 left_greater=0,
                                 right_greater=0))

    def compair_ne(
            self,
            other:
        'MultisetExpression[T_contra] | Mapping[T_contra, int] | Sequence[T_contra]',
            *,
            order: Order = Order.Descending):
        """Evaluation: EXPERIMENTAL: Compare pairs of elements in sorted order, counting how many pairs `self` is >= `other`.

        Any extra unpaired elements do not affect the result.

        Args:
            other: The other multiset to compare.
            order: Which order elements will be matched in.
                Default is descending.
        """
        other = implicit_convert_to_expression(other)
        return self.evaluate(other,
                             evaluator=icepool.evaluator.CompairEvalautor(
                                 order=order,
                                 tie=0,
                                 left_greater=1,
                                 right_greater=1))
