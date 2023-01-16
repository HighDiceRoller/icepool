__docformat__ = 'google'

import icepool
import icepool.expression

from icepool.typing import Order, Outcome

from abc import ABC, abstractmethod
from functools import cached_property, reduce
from typing import Callable, Collection, Hashable, Mapping, Sequence, Type, TypeAlias, TypeVar

T = TypeVar('T', bound=Outcome)
"""Type variable representing an outcome type."""

U = TypeVar('U', bound=Outcome)
"""Type variable representing another outcome type."""


class MultisetExpression(ABC):
    """Abstract base class representing an expression that operates on multisets.

    Use `MultisetVariable` to start an expression.

    Use the provided operators and methods to build up more complicated
    expressions, or to attach a final evaluator.
    """

    @abstractmethod
    def next_state(self, state, outcome: Outcome, bound_counts: tuple[int, ...],
                   counts: tuple[int, ...]) -> tuple[Hashable, int]:
        """Updates the state for this expression and does any necessary count modification.

        Args:
            state: The overall state. This will contain all information needed
                by this expression and any previous expressions.
            outcome: The current outcome.
            counts: The raw counts originating from the free variables.
                This must be passed to any previous expressions.
            bound_counts: The counts originating from bound generators, in the
                same order as they were returned from `bound_generators()`.
                Each sub-expression will split this tuple until each
                bound generator expression receives just its own count.

        Returns:
            state: The updated state, which will be seen again by this
            `next_state` later.
            count: The resulting count, which will be sent forward.
        """

    @abstractmethod
    def order(self) -> Order:
        """Any ordering that is required by this expression.

        This should check any previous expressions for their order, and
        raise a ValueError for any incompatibilities.

        Returns:
            The required order.
        """

    @property
    @abstractmethod
    def arity(self) -> int:
        """The minimum number of multisets/counts that must be provided to this expression.

        Any excess multisets/counts that are provided will be ignored.

        This does not include bound generators.
        """

    @abstractmethod
    def bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        """Returns a sequence of bound generators."""

    # Binary operators.

    def __add__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(self, other)

    def __radd__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(other, self)

    def disjoint_sum(self,
                     *others: 'MultisetExpression') -> 'MultisetExpression':
        return reduce(operator.add, others, self)  # type: ignore

    def __sub__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DifferenceExpression(self, other)

    def __rsub__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DifferenceExpression(other, self)

    def difference(self, *others: 'MultisetExpression') -> 'MultisetExpression':
        return reduce(operator.sub, others, self)  # type: ignore

    def __and__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.IntersectionExpression(self, other)

    def __rand__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.IntersectionExpression(other, self)

    def intersection(self,
                     *others: 'MultisetExpression') -> 'MultisetExpression':
        return reduce(operator.and_, others, self)  # type: ignore

    def __or__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.UnionExpression(self, other)

    def __ror__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.UnionExpression(other, self)

    def union(self, *others: 'MultisetExpression') -> 'MultisetExpression':
        return reduce(operator.or_, others, self)  # type: ignore

    def __xor__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(self, other)

    def __rxor__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(other, self)

    def symmetric_difference(
            self, other: 'MultisetExpression') -> 'MultisetExpression':
        return icepool.expression.SymmetricDifferenceExpression(self, other)

    # Adjust counts.

    def __mul__(self, other: int) -> 'MultisetExpression':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, other)

    # Commutable in this case.
    def __rmul__(self, other: int) -> 'MultisetExpression':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, other)

    def multiply_counts(self, constant: int, /) -> 'MultisetExpression':
        """Multiplies all counts by a constant.

        Same as `self * constant`.
        """
        return self * constant

    def __floordiv__(self, other: int) -> 'MultisetExpression':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.FloorDivCountsExpression(self, other)

    def divide_counts(self, constant: int, /) -> 'MultisetExpression':
        """Divides all counts by a constant (rounding down).

        Same as `self // constant`.
        """
        return self // constant

    def filter_counts(self, min_count: int) -> 'MultisetExpression':
        """Counts less than `min_count` are treated as zero.

        For example, `generator.filter_counts(2)` would only produce
        pairs and better.
        """
        return icepool.expression.FilterCountsExpression(self, min_count)

    def unique(self, max_count: int = 1) -> 'MultisetExpression':
        """Counts each outcome at most `max_count` times.

        For example, `generator.unique(2)` would count each outcome at most
        twice.
        """
        return icepool.expression.UniqueExpression(self, max_count)

    # Evaluations.

    def evaluate(
        *expressions: 'MultisetExpression',
        evaluator: 'icepool.MultisetEvaluator[T, U]'
    ) -> 'icepool.MultisetEvaluator[T,  U]':
        """Attaches a final `MultisetEvaluator` to expressions.

        The result is an `MultisetEvaluator` that runs the expressions
        before sending the results to the provided evaluator.
        """
        return icepool.expression.ExpressionEvaluator(*expressions,
                                                      evaluator=evaluator)

    def expand(self) -> 'icepool.MultisetEvaluator[T,  tuple[T, ...]]':
        """All possible sorted tuples of outcomes.

        This is expensive and not recommended unless there are few possibilities.
        """
        evaluator = icepool.evaluator.ExpandEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def sum(
        self,
        map: Callable[[T], U] | Mapping[T, U] | None = None
    ) -> 'icepool.MultisetEvaluator[T, U]':
        evaluator = icepool.evaluator.SumEvaluator(map)
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def count(self) -> 'icepool.MultisetEvaluator[Outcome, int]':
        """The total count over all outcomes.

        This is usually not very interesting unless some other operation is
        performed first. Examples:

        `generator.unique().count()` will count the number of unique outcomes.

        `(generator & [4, 5, 6]).count()` will count up to one each of
        4, 5, and 6.
        """
        evaluator = icepool.evaluator.count_evaluator
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def highest_outcome_and_count(
            self) -> 'icepool.MultisetEvaluator[T, tuple[T, int]]':
        """The highest outcome with positive count, along with that count.

        If no outcomes have positive count, an arbitrary outcome will be
        produced with a 0 count.
        """
        evaluator = icepool.evaluator.HighestOutcomeAndCountEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def all_counts(
        self,
        positive_only: bool = True
    ) -> 'icepool.MultisetEvaluator[T, tuple[int, ...]]':
        """Produces a tuple of all counts, i.e. the sizes of all matching sets.

        Args:
            positive_only: If `True` (default), negative and zero counts
                will be omitted.
        """
        evaluator = icepool.evaluator.AllCountsEvaluator(
            positive_only=positive_only)
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def largest_count(self) -> 'icepool.MultisetEvaluator[T, int]':
        """The size of the largest matching set among the outcomes."""
        evaluator = icepool.evaluator.LargestCountEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def largest_count_and_outcome(
            self) -> 'icepool.MultisetEvaluator[T, tuple[int, T]]':
        """The largest matching set among the outcomes and its outcome."""
        evaluator = icepool.evaluator.LargestCountAndOutcomeEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def largest_straight(self) -> 'icepool.MultisetEvaluator[int, int]':
        """The size of the largest straight among the outcomes.

        Outcomes must be `int`s.
        """
        evaluator = icepool.evaluator.LargestStraightEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    def largest_straight_and_outcome(
            self) -> 'icepool.MultisetEvaluator[int, tuple[int, int]]':
        """The size of the largest straight among the outcomes and the highest outcome in that straight.

        Outcomes must be `int`s.
        """
        evaluator = icepool.evaluator.LargestStraightAndOutcomeEvaluator()
        return icepool.expression.ExpressionEvaluator(self, evaluator=evaluator)

    # Comparators.

    def compare(
        self, right: 'MultisetExpression | Mapping[T, int] | Collection[T]',
        operation_class: Type['icepool.evaluator.ComparisonEvaluator']
    ) -> 'icepool.MultisetEvaluator[T, bool]':
        if isinstance(right, MultisetExpression):
            return icepool.expression.ExpressionEvaluator(
                self, right, evaluator=operation_class())
        elif isinstance(right, (Mapping, Collection)):
            right_expression = icepool.expression.BoundGeneratorExpression(
                icepool.implicit_convert_to_generator(right))
            return icepool.expression.ExpressionEvaluator(
                self, right_expression, evaluator=operation_class())
        else:
            raise TypeError('Right side is not comparable.')

    def __lt__(self,
               other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
               /) -> 'icepool.MultisetEvaluator[T, bool]':
        try:
            return self.compare(other,
                                icepool.evaluator.IsProperSubsetEvaluator)
        except TypeError:
            return NotImplemented

    def __le__(self,
               other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
               /) -> 'icepool.MultisetEvaluator[T, bool]':
        try:
            return self.compare(other, icepool.evaluator.IsSubsetEvaluator)
        except TypeError:
            return NotImplemented

    def issubset(self,
                 other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
                 /) -> 'icepool.MultisetEvaluator[T, bool]':
        """Whether the outcome multiset is a subset of the other multiset.

        Same as `self <= other`.
        """
        return self.compare(other, icepool.evaluator.IsSubsetEvaluator)

    def __gt__(self,
               other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
               /) -> 'icepool.MultisetEvaluator[T, bool]':
        try:
            return self.compare(other,
                                icepool.evaluator.IsProperSupersetEvaluator)
        except TypeError:
            return NotImplemented

    def __ge__(self,
               other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
               /) -> 'icepool.MultisetEvaluator[T, bool]':
        try:
            return self.compare(other, icepool.evaluator.IsSupersetEvaluator)
        except TypeError:
            return NotImplemented

    def issuperset(
            self, other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
            /) -> 'icepool.MultisetEvaluator[T, bool]':
        """Whether the outcome multiset is a superset of the target multiset.

        Same as `self >= other`.
        """
        return self.compare(other, icepool.evaluator.IsSupersetEvaluator)

    # The result has no truth value.
    def __eq__(  # type: ignore
            self, other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
            /) -> 'icepool.MultisetEvaluator[T, bool]':
        try:
            return self.compare(other, icepool.evaluator.IsEqualSetEvaluator)
        except TypeError:
            return NotImplemented

    # The result has no truth value.
    def __ne__(  # type: ignore
            self, other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
            /) -> 'icepool.MultisetEvaluator[T, bool]':
        try:
            return self.compare(other, icepool.evaluator.IsNotEqualSetEvaluator)
        except TypeError:
            return NotImplemented

    def isdisjoint(
            self, other: 'MultisetExpression | Mapping[T, int] | Collection[T]',
            /) -> 'icepool.MultisetEvaluator[T, bool]':
        """Whether the outcome multiset is disjoint from the target multiset."""
        return self.compare(other, icepool.evaluator.IsDisjointSetEvaluator)
