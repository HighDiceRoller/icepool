__docformat__ = 'google'

from abc import abstractmethod
import icepool
from icepool.expand import Expandable
from icepool.expression.multiset_expression_base import Q, Dungeonlet, MultisetExpressionBase
from icepool.collection.counts import Counts
from icepool.order import Order
from icepool.population.keep import highest_slice, lowest_slice

import operator

from icepool.typing import T, U, MaybeHashKeyed, ImplicitConversionError
from types import EllipsisType
from typing import (TYPE_CHECKING, Callable, Collection, Literal, Mapping,
                    Sequence, Type, cast, overload)

if TYPE_CHECKING:
    from icepool.evaluator.multiset_function import MultisetFunctionRawResult
    from icepool.expression.multiset_tuple_expression import MultisetTupleExpression, IntTupleOut
    from icepool.expression.multiset_parameter import MultisetParameter


@overload
def implicit_convert_to_expression(
    arg: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
) -> 'MultisetExpression[T]':
    ...


@overload
def implicit_convert_to_expression(
    arg: 'MultisetTupleExpression[T, IntTupleOut]'
) -> 'MultisetTupleExpression[T, IntTupleOut]':
    ...


@overload
def implicit_convert_to_expression(
    arg: 'MultisetExpressionBase | Mapping[T, int] | Sequence[T]'
) -> 'MultisetExpression[T] | MultisetTupleExpression[T, IntTupleOut]':
    ...


def implicit_convert_to_expression(
    arg: 'MultisetExpressionBase[T, Q] | Mapping[T, int] | Sequence[T]'
) -> 'MultisetExpressionBase[T, Q]':
    """Implcitly converts the argument to a `MultisetExpression` with `int` counts.

    Args:
        arg: The argument must either already be a `MultisetExpression`;
            or a `Mapping` or `Collection`.
    """
    if isinstance(arg, MultisetExpressionBase):
        return arg
    elif isinstance(arg, (Mapping, Sequence)):
        return icepool.Pool(arg)  # type: ignore
    else:
        raise ImplicitConversionError(
            f'Argument of type {arg.__class__.__name__} cannot be implicitly converted to a Pool.'
        )


class MultisetExpression(MultisetExpressionBase[T, int],
                         Expandable[tuple[T, ...]]):
    """Abstract base class representing an expression that operates on single multisets.

    There are three types of multiset expressions:

    * `MultisetGenerator`, which produce raw outcomes and counts.
    * `MultisetOperator`, which takes outcomes with one or more counts and
        produces a count.
    * `MultisetVariable`, which is a temporary placeholder for some other 
        expression.

    Expression methods can be applied to `MultisetGenerator`s to do simple
    evaluations. For joint evaluations, try `multiset_function`.

    Use the provided operations to build up more complicated
    expressions, or to attach a final evaluator.

    Operations include:

    | Operation                   | Count / notes                               |
    |:----------------------------|:--------------------------------------------|
    | `additive_union`, `+`       | `l + r`                                     |
    | `difference`, `-`           | `l - r`                                     |
    | `intersection`, `&`         | `min(l, r)`                                 |
    | `union`, `\\|`               | `max(l, r)`                                 |
    | `symmetric_difference`, `^` | `abs(l - r)`                                |
    | `multiply_counts`, `*`      | `count * n`                                 |
    | `divide_counts`, `//`       | `count // n`                                |
    | `modulo_counts`, `%`        | `count % n`                                 |
    | `keep_counts`               | `count if count >= n else 0` etc.           |
    | unary `+`                   | same as `keep_counts_ge(0)`                 |
    | unary `-`                   | reverses the sign of all counts             |
    | `unique`                    | `min(count, n)`                             |
    | `keep_outcomes`             | `count if outcome in t else 0`              |
    | `drop_outcomes`             | `count if outcome not in t else 0`          |
    | `map_counts`                | `f(outcome, *counts)`                       |
    | `keep`, `[]`                | less capable than `KeepGenerator` version   |
    | `highest`                   | less capable than `KeepGenerator` version   |
    | `lowest`                    | less capable than `KeepGenerator` version   |

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

    def _make_param(self, index: int, name: str) -> 'MultisetParameter[T]':
        return icepool.MultisetParameter(index, name)

    @property
    def _items_for_cartesian_product(
            self) -> Sequence[tuple[tuple[T, ...], int]]:
        expansion = cast('icepool.Die[tuple[T, ...]]', self.expand())
        return expansion.items()

    # We need to reiterate this since we override __eq__.
    __hash__ = MaybeHashKeyed.__hash__  # type: ignore

    # Binary operators.

    def __add__(self,
                other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
                /) -> 'MultisetExpression[T]':
        try:
            return MultisetExpression.additive_union(self, other)
        except ImplicitConversionError:
            return NotImplemented

    def __radd__(
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'MultisetExpression[T]':
        try:
            return MultisetExpression.additive_union(other, self)
        except ImplicitConversionError:
            return NotImplemented

    def additive_union(
        *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        """The combined elements from all of the multisets.

        Same as `a + b + c + ...`.

        Any resulting counts that would be negative are set to zero.

        Example:
        ```python
        [1, 2, 2, 3] + [1, 2, 4] -> [1, 1, 2, 2, 2, 3, 4]
        ```
        """
        expressions = tuple(
            implicit_convert_to_expression(arg) for arg in args)
        return icepool.operator.MultisetAdditiveUnion(*expressions)

    def __sub__(self,
                other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
                /) -> 'MultisetExpression[T]':
        try:
            return MultisetExpression.difference(self, other)
        except ImplicitConversionError:
            return NotImplemented

    def __rsub__(
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'MultisetExpression[T]':
        try:
            return MultisetExpression.difference(other, self)
        except ImplicitConversionError:
            return NotImplemented

    def difference(
        *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        """The elements from the left multiset that are not in any of the others.

        Same as `a - b - c - ...`.

        Any resulting counts that would be negative are set to zero.

        Example:
        ```python
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
        return icepool.operator.MultisetDifference(*expressions)

    def __and__(self,
                other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
                /) -> 'MultisetExpression[T]':
        try:
            return MultisetExpression.intersection(self, other)
        except ImplicitConversionError:
            return NotImplemented

    def __rand__(
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'MultisetExpression[T]':
        try:
            return MultisetExpression.intersection(other, self)
        except ImplicitConversionError:
            return NotImplemented

    def intersection(
        *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        """The elements that all the multisets have in common.

        Same as `a & b & c & ...`.

        Any resulting counts that would be negative are set to zero.

        Example:
        ```python
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
        return icepool.operator.MultisetIntersection(*expressions)

    def __or__(self,
               other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
               /) -> 'MultisetExpression[T]':
        try:
            return MultisetExpression.union(self, other)
        except ImplicitConversionError:
            return NotImplemented

    def __ror__(self,
                other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
                /) -> 'MultisetExpression[T]':
        try:
            return MultisetExpression.union(other, self)
        except ImplicitConversionError:
            return NotImplemented

    def union(
        *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T]':
        """The most of each outcome that appear in any of the multisets.

        Same as `a | b | c | ...`.

        Any resulting counts that would be negative are set to zero.

        Example:
        ```python
        [1, 2, 2, 3] | [1, 2, 4] -> [1, 2, 2, 3, 4]
        ```
        """
        expressions = tuple(
            implicit_convert_to_expression(arg) for arg in args)
        return icepool.operator.MultisetUnion(*expressions)

    def __xor__(self,
                other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
                /) -> 'MultisetExpression[T]':
        try:
            return MultisetExpression.symmetric_difference(self, other)
        except ImplicitConversionError:
            return NotImplemented

    def __rxor__(
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'MultisetExpression[T]':
        try:
            # Symmetric.
            return MultisetExpression.symmetric_difference(self, other)
        except ImplicitConversionError:
            return NotImplemented

    def symmetric_difference(
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'MultisetExpression[T]':
        """The elements that appear in the left or right multiset but not both.

        Same as `a ^ b`.

        Specifically, this produces the absolute difference between counts.
        If you don't want negative counts to be used from the inputs, you can
        do `+left ^ +right`.

        Example:
        ```python
        [1, 2, 2, 3] ^ [1, 2, 4] -> [2, 3, 4]
        ```
        """
        return icepool.operator.MultisetSymmetricDifference(
            self, implicit_convert_to_expression(other))

    def keep_outcomes(
            self, target:
        'Callable[[T], bool] | Collection[T] | MultisetExpression[T]',
            /) -> 'MultisetExpression[T]':
        """Keeps the elements in the target set of outcomes, and drops the rest by setting their counts to zero.

        This is similar to `intersection()`, except the right side is considered
        to have unlimited multiplicity.

        Args:
            target: A callable returning `True` iff the outcome should be kept,
                or an expression or collection of outcomes to keep.
        """
        if isinstance(target, MultisetExpression):
            return icepool.operator.MultisetFilterOutcomesBinary(self, target)
        else:
            return icepool.operator.MultisetFilterOutcomes(self, target=target)

    def drop_outcomes(
            self, target:
        'Callable[[T], bool] | Collection[T] | MultisetExpression[T]',
            /) -> 'MultisetExpression[T]':
        """Drops the elements in the target set of outcomes by setting their counts to zero, and keeps the rest.

        This is similar to `difference()`, except the right side is considered
        to have unlimited multiplicity.

        Args:
            target: A callable returning `True` iff the outcome should be
                dropped, or an expression or collection of outcomes to drop.
        """
        if isinstance(target, MultisetExpression):
            return icepool.operator.MultisetFilterOutcomesBinary(self,
                                                                 target,
                                                                 invert=True)
        else:
            return icepool.operator.MultisetFilterOutcomes(self,
                                                           target=target,
                                                           invert=True)

    # Adjust counts.

    def map_counts(*args:
                   'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
                   function: Callable[..., int]) -> 'MultisetExpression[T]':
        """Maps the counts to new counts.

        Args:
            function: A function that takes `outcome, *counts` and produces a
                combined count.
        """
        expressions = tuple(
            implicit_convert_to_expression(arg) for arg in args)
        return icepool.operator.MultisetMapCounts(*expressions,
                                                  function=function)

    def __mul__(self, n: int) -> 'MultisetExpression[T]':
        if not isinstance(n, int):
            return NotImplemented
        return self.multiply_counts(n)

    # Commutable in this case.
    def __rmul__(self, n: int) -> 'MultisetExpression[T]':
        if not isinstance(n, int):
            return NotImplemented
        return self.multiply_counts(n)

    def multiply_counts(self, n: int, /) -> 'MultisetExpression[T]':
        """Multiplies all counts by n.

        Same as `self * n`.

        Example:
        ```python
        Pool([1, 2, 2, 3]) * 2 -> [1, 1, 2, 2, 2, 2, 3, 3]
        ```
        """
        return icepool.operator.MultisetMultiplyCounts(self, constant=n)

    @overload
    def __floordiv__(self, other: int) -> 'MultisetExpression[T]':
        ...

    @overload
    def __floordiv__(
        self, other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'icepool.Die[int] | MultisetFunctionRawResult[T, int]':
        """Same as divide_counts()."""

    @overload
    def __floordiv__(
        self,
        other: 'int | MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T] | icepool.Die[int] | MultisetFunctionRawResult[T, int]':
        """Same as count_subset()."""

    def __floordiv__(
        self,
        other: 'int | MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'MultisetExpression[T] | icepool.Die[int] | MultisetFunctionRawResult[T, int]':
        if isinstance(other, int):
            return self.divide_counts(other)
        else:
            return self.count_subset(other)

    def divide_counts(self, n: int, /) -> 'MultisetExpression[T]':
        """Divides all counts by n (rounding down).

        Same as `self // n`.

        Example:
        ```python
        Pool([1, 2, 2, 3]) // 2 -> [2]
        ```
        """
        return icepool.operator.MultisetFloordivCounts(self, constant=n)

    def __mod__(self, n: int, /) -> 'MultisetExpression[T]':
        if not isinstance(n, int):
            return NotImplemented
        return icepool.operator.MultisetModuloCounts(self, constant=n)

    def modulo_counts(self, n: int, /) -> 'MultisetExpression[T]':
        """Moduos all counts by n.

        Same as `self % n`.

        Example:
        ```python
        Pool([1, 2, 2, 3]) % 2 -> [1, 3]
        ```
        """
        return self % n

    def __pos__(self) -> 'MultisetExpression[T]':
        """Sets all negative counts to zero."""
        return icepool.operator.MultisetKeepCounts(self,
                                                   comparison='>=',
                                                   constant=0)

    def __neg__(self) -> 'MultisetExpression[T]':
        """As -1 * self."""
        return -1 * self

    def keep_counts(self, comparison: Literal['==', '!=', '<=', '<', '>=',
                                              '>'], n: int,
                    /) -> 'MultisetExpression[T]':
        """Keeps counts fitting the comparison, treating the rest as zero.

        For example, `expression.keep_counts('>=', 2)` would keep pairs,
        triplets, etc. and drop singles.

        ```python
        Pool([1, 2, 2, 3, 3, 3]).keep_counts('>=', 2) -> [2, 2, 3, 3, 3]
        ```
        
        Args:
            comparison: The comparison to use.
            n: The number to compare counts against.
        """
        return icepool.operator.MultisetKeepCounts(self,
                                                   comparison=comparison,
                                                   constant=n)

    def unique(self, n: int = 1, /) -> 'MultisetExpression[T]':
        """Counts each outcome at most `n` times.

        For example, `generator.unique(2)` would count each outcome at most
        twice.

        Example:
        ```python
        Pool([1, 2, 2, 3]).unique() -> [1, 2, 3]
        ```
        """
        return icepool.operator.MultisetUnique(self, constant=n)

    # Keep highest / lowest.

    @overload
    def keep(
        self, index: slice | Sequence[int | EllipsisType]
    ) -> 'MultisetExpression[T]':
        ...

    @overload
    def keep(self,
             index: int) -> 'icepool.Die[T] | MultisetFunctionRawResult[T, T]':
        ...

    def keep(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'MultisetExpression[T] | icepool.Die[T] | MultisetFunctionRawResult[T, T]':
        """Selects elements after drawing and sorting.

        This is less capable than the `KeepGenerator` version.
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
            index. In this case the result is a `Die`.

        Negative incoming counts are treated as zero counts.

        Use the `[]` operator for the same effect as this method.
        """
        if isinstance(index, int):
            return icepool.evaluator.keep_evaluator.evaluate(self, index=index)
        else:
            return icepool.operator.MultisetKeep(self, index=index)

    @overload
    def __getitem__(
        self, index: slice | Sequence[int | EllipsisType]
    ) -> 'MultisetExpression[T]':
        ...

    @overload
    def __getitem__(
            self,
            index: int) -> 'icepool.Die[T] | MultisetFunctionRawResult[T, T]':
        ...

    def __getitem__(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'MultisetExpression[T] | icepool.Die[T] | MultisetFunctionRawResult[T, T]':
        return self.keep(index)

    def lowest(self,
               keep: int | None = None,
               drop: int | None = None) -> 'MultisetExpression[T]':
        """Keep some of the lowest elements from this multiset and drop the rest.

        In contrast to the die and free function versions, this does not
        automatically sum the dice. Use `.sum()` afterwards if you want to sum.
        Alternatively, you can perform some other evaluation.

        This requires the outcomes to be evaluated in ascending order.

        Args:
            keep, drop: These arguments work together:
                * If neither are provided, the single lowest element
                    will be kept.
                * If only `keep` is provided, the `keep` lowest elements
                    will be kept.
                * If only `drop` is provided, the `drop` lowest elements
                    will be dropped and the rest will be kept.
                * If both are provided, `drop` lowest elements will be dropped,
                    then the next `keep` lowest elements will be kept.
        """
        index = lowest_slice(keep, drop)
        return self.keep(index)

    def highest(self,
                keep: int | None = None,
                drop: int | None = None) -> 'MultisetExpression[T]':
        """Keep some of the highest elements from this multiset and drop the rest.

        In contrast to the die and free function versions, this does not
        automatically sum the dice. Use `.sum()` afterwards if you want to sum.
        Alternatively, you can perform some other evaluation.

        This requires the outcomes to be evaluated in descending order.

        Args:
            keep, drop: These arguments work together:
                * If neither are provided, the single highest element
                    will be kept.
                * If only `keep` is provided, the `keep` highest elements
                    will be kept.
                * If only `drop` is provided, the `drop` highest elements
                    will be dropped and the rest will be kept.
                * If both are provided, `drop` highest elements will be dropped, 
                    then the next `keep` highest elements will be kept.
        """
        index = highest_slice(keep, drop)
        return self.keep(index)

    # Matching.

    def sort_match(self,
                   comparison: Literal['==', '!=', '<=', '<', '>=', '>'],
                   other: 'MultisetExpression[T]',
                   /,
                   order: Order = Order.Descending) -> 'MultisetExpression[T]':
        """EXPERIMENTAL: Matches elements of `self` with elements of `other` in sorted order, then keeps elements from `self` that fit `comparison` with their partner.

        Extra elements: If `self` has more elements than `other`, whether the
        extra elements are kept depends on the `order` and `comparison`:
        * Descending: kept for `'>='`, `'>'`
        * Ascending: kept for `'<='`, `'<'`

        Example: An attacker rolls 3d6 versus a defender's 2d6 in the game of
        *RISK*. Which pairs did the attacker win?
        ```python
        d6.pool(3).highest(2).sort_match('>', d6.pool(2))
        ```
        
        Suppose the attacker rolled 6, 4, 3 and the defender 5, 5.
        In this case the 4 would be blocked since the attacker lost that pair,
        leaving the attacker's 6 and 3. If you don't want to keep the extra
        element, you can use `highest`.
        ```python
        Pool([6, 4, 3]).sort_match('>', [5, 5]) -> [6, 3]
        Pool([6, 4, 3]).highest(2).sort_match('>', [5, 5]) -> [6]
        ```

        Contrast `maximum_match()`, which first creates the maximum number of
        pairs that fit the comparison, not necessarily in sorted order.
        In the above example, `maximum_match()` would allow the defender to
        assign their 5s to block both the 4 and the 3.

        Negative incoming counts are treated as zero counts.
        
        Args:
            comparison: The comparison to filter by. If you want to drop rather
                than keep, use the complementary comparison:
                * `'=='` vs. `'!='`
                * `'<='` vs. `'>'`
                * `'>='` vs. `'<'`
            other: The other multiset to match elements with.
            order: The order in which to sort before forming matches.
                Default is descending.
        """
        other = implicit_convert_to_expression(other)

        match comparison:
            case '==':
                lesser, tie, greater = 0, 1, 0
            case '!=':
                lesser, tie, greater = 1, 0, 1
            case '<=':
                lesser, tie, greater = 1, 1, 0
            case '<':
                lesser, tie, greater = 1, 0, 0
            case '>=':
                lesser, tie, greater = 0, 1, 1
            case '>':
                lesser, tie, greater = 0, 0, 1
            case _:
                raise ValueError(f'Invalid comparison {comparison}')

        if order > 0:
            left_first = lesser
            right_first = greater
        else:
            left_first = greater
            right_first = lesser

        return icepool.operator.MultisetSortMatch(self,
                                                  other,
                                                  order=order,
                                                  tie=tie,
                                                  left_first=left_first,
                                                  right_first=right_first)

    def maximum_match_highest(
            self, comparison: Literal['<=',
                                      '<'], other: 'MultisetExpression[T]', /,
            *, keep: Literal['matched',
                             'unmatched']) -> 'MultisetExpression[T]':
        """EXPERIMENTAL: Match the highest elements from `self` with even higher (or equal) elements from `other`.

        This matches elements of `self` with elements of `other`, such that in
        each pair the element from `self` fits the `comparision` with the
        element from `other`. As many such pairs of elements will be matched as 
        possible, preferring the highest matchable elements of `self`.
        Finally, either the matched or unmatched elements from `self` are kept.

        This requires that outcomes be evaluated in descending order.

        Example: An attacker rolls a pool of 4d6 and a defender rolls a pool of 
        3d6. Defender dice can be used to block attacker dice of equal or lesser
        value, and the defender prefers to block the highest attacker dice
        possible. Which attacker dice were not blocked?
        ```python
        d6.pool(4).maximum_match('<=', d6.pool(3), keep='unmatched').sum()
        ```

        Suppose the attacker rolls 6, 4, 3, 1 and the defender rolls 5, 5.
        Then the result would be [6, 1].
        ```python
        d6.pool([6, 4, 3, 1]).maximum_match('<=', [5, 5], keep='unmatched')
        -> [6, 1]
        ```

        Contrast `sort_match()`, which first creates pairs in
        sorted order and then filters them by `comparison`.
        In the above example, `sort_matched` would force the defender to match
        against the 5 and the 4, which would only allow them to block the 4.

        Negative incoming counts are treated as zero counts.

        Args:
            comparison: Either `'<='` or `'<'`.
            other: The other multiset to match elements with.
            keep: Whether 'matched' or 'unmatched' elements are to be kept.
        """
        if keep == 'matched':
            keep_boolean = True
        elif keep == 'unmatched':
            keep_boolean = False
        else:
            raise ValueError(f"keep must be either 'matched' or 'unmatched'")

        other = implicit_convert_to_expression(other)
        match comparison:
            case '<=':
                match_equal = True
            case '<':
                match_equal = False
            case _:
                raise ValueError(f'Invalid comparison {comparison}')
        return icepool.operator.MultisetMaximumMatch(self,
                                                     other,
                                                     order=Order.Descending,
                                                     match_equal=match_equal,
                                                     keep=keep_boolean)

    def maximum_match_lowest(
            self, comparison: Literal['>=',
                                      '>'], other: 'MultisetExpression[T]', /,
            *, keep: Literal['matched',
                             'unmatched']) -> 'MultisetExpression[T]':
        """EXPERIMENTAL: Match the lowest elements from `self` with even lower (or equal) elements from `other`.

        This matches elements of `self` with elements of `other`, such that in
        each pair the element from `self` fits the `comparision` with the
        element from `other`. As many such pairs of elements will be matched as 
        possible, preferring the lowest matchable elements of `self`.
        Finally, either the matched or unmatched elements from `self` are kept.

        This requires that outcomes be evaluated in ascending order.

        Contrast `sort_match()`, which first creates pairs in
        sorted order and then filters them by `comparison`.

        Args:
            comparison: Either `'>='` or `'>'`.
            other: The other multiset to match elements with.
            keep: Whether 'matched' or 'unmatched' elements are to be kept.
        """
        if keep == 'matched':
            keep_boolean = True
        elif keep == 'unmatched':
            keep_boolean = False
        else:
            raise ValueError(f"keep must be either 'matched' or 'unmatched'")

        other = implicit_convert_to_expression(other)
        match comparison:
            case '>=':
                match_equal = True
            case '>':
                match_equal = False
            case _:
                raise ValueError(f'Invalid comparison {comparison}')
        return icepool.operator.MultisetMaximumMatch(self,
                                                     other,
                                                     order=Order.Ascending,
                                                     match_equal=match_equal,
                                                     keep=keep_boolean)

    # Evaluations.

    def expand(
        self,
        order: Order = Order.Ascending
    ) -> 'icepool.Die[tuple[T, ...]] | MultisetFunctionRawResult[T, tuple[T, ...]]':
        """Evaluation: All elements of the multiset in ascending order.

        This is expensive and not recommended unless there are few possibilities.

        Args:
            order: Whether the elements are in ascending (default) or descending
                order.
        """
        return icepool.evaluator.ExpandEvaluator().evaluate(self, order=order)

    def sum(
        self,
        map: Callable[[T], U] | Mapping[T, U] | None = None
    ) -> 'icepool.Die[U] | MultisetFunctionRawResult[T, U]':
        """Evaluation: The sum of all elements."""
        if map is None:
            return icepool.evaluator.sum_evaluator.evaluate(self)
        else:
            return icepool.evaluator.SumEvaluator(map).evaluate(self)

    def size(self) -> 'icepool.Die[int] | MultisetFunctionRawResult[T, int]':
        """Evaluation: The total number of elements in the multiset.

        This is usually not very interesting unless some other operation is
        performed first. Examples:

        `generator.unique().size()` will count the number of unique outcomes.

        `(generator & [4, 5, 6]).size()` will count up to one each of
        4, 5, and 6.
        """
        return icepool.evaluator.size_evaluator.evaluate(self)

    def any(self) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        """Evaluation: Whether the multiset has at least one positive count. """
        return icepool.evaluator.any_evaluator.evaluate(self)

    def highest_outcome_and_count(
        self
    ) -> 'icepool.Die[tuple[T, int]] | MultisetFunctionRawResult[T, tuple[T, int]]':
        """Evaluation: The highest outcome with positive count, along with that count.

        If no outcomes have positive count, the min outcome will be returned with 0 count.
        """
        return icepool.evaluator.highest_outcome_and_count_evaluator.evaluate(
            self)

    def all_counts(
        self,
        filter: int | Literal['all'] = 1
    ) -> 'icepool.Die[tuple[int, ...]] | MultisetFunctionRawResult[T, tuple[int, ...]]':
        """Evaluation: Sorted tuple of all counts, i.e. the sizes of all matching sets.

        The sizes are in **descending** order.

        Args:
            filter: Any counts below this value will not be in the output.
                For example, `filter=2` will only produce pairs and better.
                If `None`, no filtering will be done.

                Why not just place `keep_counts_ge()` before this?
                `keep_counts_ge()` operates by setting counts to zero, so you
                would still need an argument to specify whether you want to
                output zero counts. So we might as well use the argument to do
                both.
        """
        return icepool.evaluator.AllCountsEvaluator(
            filter=filter).evaluate(self)

    def largest_count(
            self) -> 'icepool.Die[int] | MultisetFunctionRawResult[T, int]':
        """Evaluation: The size of the largest matching set among the elements."""
        return icepool.evaluator.largest_count_evaluator.evaluate(self)

    def largest_count_and_outcome(
        self
    ) -> 'icepool.Die[tuple[int, T]] | MultisetFunctionRawResult[T, tuple[int, T]]':
        """Evaluation: The largest matching set among the elements and the corresponding outcome."""
        return icepool.evaluator.largest_count_and_outcome_evaluator.evaluate(
            self)

    def __rfloordiv__(
        self, other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]'
    ) -> 'icepool.Die[int] | MultisetFunctionRawResult[T, int]':
        return implicit_convert_to_expression(other).count_subset(self)

    def count_subset(
        self,
        divisor: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
        /,
        *,
        empty_divisor: int | None = None
    ) -> 'icepool.Die[int] | MultisetFunctionRawResult[T, int]':
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
        return icepool.evaluator.CountSubsetEvaluator(
            empty_divisor=empty_divisor).evaluate(self, divisor)

    def largest_straight(
        self: 'MultisetExpression[int]'
    ) -> 'icepool.Die[int] | MultisetFunctionRawResult[int, int]':
        """Evaluation: The size of the largest straight among the elements.

        Outcomes must be `int`s.
        """
        return icepool.evaluator.largest_straight_evaluator.evaluate(self)

    def largest_straight_and_outcome(
        self: 'MultisetExpression[int]',
        priority: Literal['low', 'high'] = 'high',
        /
    ) -> 'icepool.Die[tuple[int, int]] | MultisetFunctionRawResult[int, tuple[int, int]]':
        """Evaluation: The size of the largest straight among the elements and the highest (optionally, lowest) outcome in that straight.

        Straight size is prioritized first, then the outcome.

        Outcomes must be `int`s.

        Args:
            priority: Controls which outcome within the straight is returned,
                and which straight is picked if there is a tie for largest
                straight.
        """
        if priority == 'high':
            return icepool.evaluator.largest_straight_and_outcome_evaluator_high.evaluate(
                self)
        elif priority == 'low':
            return icepool.evaluator.largest_straight_and_outcome_evaluator_low.evaluate(
                self)
        else:
            raise ValueError("priority must be 'low' or 'high'.")

    def all_straights(
        self: 'MultisetExpression[int]'
    ) -> 'icepool.Die[tuple[int, ...]] | MultisetFunctionRawResult[int, tuple[int, ...]]':
        """Evaluation: The sizes of all straights.

        The sizes are in **descending** order.

        Each element can only contribute to one straight, though duplicate
        elements can produces straights that overlap in outcomes. In this case,
        elements are preferentially assigned to the longer straight.
        """
        return icepool.evaluator.all_straights_evaluator.evaluate(self)

    def all_straights_reduce_counts(
        self: 'MultisetExpression[int]',
        reducer: Callable[[int, int], int] = operator.mul
    ) -> 'icepool.Die[tuple[tuple[int, int], ...]] | MultisetFunctionRawResult[int, tuple[tuple[int, int], ...]]':
        """Experimental: All straights with a reduce operation on the counts.

        This can be used to evaluate e.g. cribbage-style straight counting.

        The result is a tuple of `(run_length, run_score)`s.
        """
        return icepool.evaluator.AllStraightsReduceCountsEvaluator(
            reducer=reducer).evaluate(self)

    def argsort(self: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
                *args: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
                order: Order = Order.Descending,
                limit: int | None = None):
        """Experimental: Returns the indexes of the originating multisets for each rank in their additive union.

        Example:
        ```python
        MultisetExpression.argsort([10, 9, 5], [9, 9])
        ```
        produces
        ```python
        ((0,), (0, 1, 1), (0,))
        ```
        
        Args:
            self, *args: The multiset expressions to be evaluated.
            order: Which order the ranks are to be emitted. Default is descending.
            limit: How many ranks to emit. Default will emit all ranks, which
                makes the length of each outcome equal to
                `additive_union(+self, +arg1, +arg2, ...).unique().size()`
        """
        self = implicit_convert_to_expression(self)
        converted_args = [implicit_convert_to_expression(arg) for arg in args]
        return icepool.evaluator.ArgsortEvaluator(order=order,
                                                  limit=limit).evaluate(
                                                      self, *converted_args)

    # Comparators.

    def _compare(
        self,
        right: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
        operation_class: Type['icepool.evaluator.ComparisonEvaluator'],
        *,
        truth_value_callback: 'Callable[[], bool] | None' = None
    ) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        right = icepool.implicit_convert_to_expression(right)

        if truth_value_callback is not None:

            def data_callback() -> Counts[bool]:
                die = cast('icepool.Die[bool]',
                           operation_class().evaluate(self, right))
                if not isinstance(die, icepool.Die):
                    raise TypeError('Did not resolve to a die.')
                return die._data

            return icepool.DieWithTruth(data_callback, truth_value_callback)
        else:
            return operation_class().evaluate(self, right)

    def __lt__(self,
               other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
               /) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        try:
            return self._compare(other,
                                 icepool.evaluator.IsProperSubsetEvaluator)
        except TypeError:
            return NotImplemented

    def __le__(self,
               other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
               /) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        try:
            return self._compare(other, icepool.evaluator.IsSubsetEvaluator)
        except TypeError:
            return NotImplemented

    def issubset(
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
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

    def __gt__(self,
               other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
               /) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        try:
            return self._compare(other,
                                 icepool.evaluator.IsProperSupersetEvaluator)
        except TypeError:
            return NotImplemented

    def __ge__(self,
               other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
               /) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        try:
            return self._compare(other, icepool.evaluator.IsSupersetEvaluator)
        except TypeError:
            return NotImplemented

    def issuperset(
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        """Evaluation: Whether this multiset is a superset of the other multiset.

        Specifically, if this multiset has a greater or equal count for each
        outcome than the other multiset, this evaluates to `True`; 
        if there is some  outcome for which this multiset has a lesser count 
        than the other multiset, this evaluates to `False`.
        
        A typical use of this evaluation is testing for the presence of a
        combo of cards in a hand, e.g.

        ```python
        deck.deal(5) >= ['a', 'a', 'b']
        ```

        represents the chance that a deal of 5 cards contains at least two 'a's
        and one 'b'.

        `issuperset` is the same as `self >= other`.

        `self > other` evaluates a proper superset relation, which is the same
        except the result is `False` if the two multisets are exactly equal.
        """
        return self._compare(other, icepool.evaluator.IsSupersetEvaluator)

    def __eq__(  # type: ignore
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        try:

            def truth_value_callback() -> bool:
                return self.equals(other)

            return self._compare(other,
                                 icepool.evaluator.IsEqualSetEvaluator,
                                 truth_value_callback=truth_value_callback)
        except TypeError:
            return NotImplemented

    def __ne__(  # type: ignore
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        try:

            def truth_value_callback() -> bool:
                return not self.equals(other)

            return self._compare(other,
                                 icepool.evaluator.IsNotEqualSetEvaluator,
                                 truth_value_callback=truth_value_callback)
        except TypeError:
            return NotImplemented

    def isdisjoint(
            self,
            other: 'MultisetExpression[T] | Mapping[T, int] | Sequence[T]',
            /) -> 'icepool.Die[bool] | MultisetFunctionRawResult[T, bool]':
        """Evaluation: Whether this multiset is disjoint from the other multiset.
        
        Specifically, this evaluates to `False` if there is any outcome for
        which both multisets have positive count, and `True` if there is not.

        Negative incoming counts are treated as zero counts.
        """
        return self._compare(other, icepool.evaluator.IsDisjointSetEvaluator)

    # For helping debugging / testing.
    def force_order(self, force_order: Order) -> 'MultisetExpression[T]':
        """Forces outcomes to be seen by the evaluator in the given order.

        This can be useful for debugging / testing.
        """
        if force_order == Order.Any:
            return self
        return icepool.operator.MultisetForceOrder(self,
                                                   force_order=force_order)
