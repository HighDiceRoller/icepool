__docformat__ = 'google'

import operator
import icepool

from typing import Hashable, Iterable, Sequence
from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Order, Outcome, T_contra

from abc import abstractmethod
from functools import cached_property, reduce


class BinaryOperatorExpression(MultisetExpression[T_contra]):

    def __init__(self, *prevs: MultisetExpression[T_contra]) -> None:
        """Constructor.

        Args:
            *prevs: Any number of expressions to feed into the operator.
                If zero expressions are provided, the result will have all zero
                counts.
                If more than two expressions are provided, the counts will be
                `reduce`d.
        """
        for prev in prevs:
            self._validate_output_arity(prev)
        self._prevs = prevs

    @staticmethod
    @abstractmethod
    def merge_counts(left: int, right: int) -> int:
        """Merge counts produced by the left and right expression."""

    @staticmethod
    @abstractmethod
    def symbol() -> str:
        """A symbol representing this operation."""

    def _next_state(self, state, outcome: T_contra, bound_counts: tuple[int,
                                                                        ...],
                    counts: tuple[int, ...]) -> tuple[Hashable, int]:
        if len(self._prevs) == 0:
            return (), 0
        prev_states = state or (None,) * len(self._prevs)

        prev_states, prev_counts = zip(*(prev._next_state(
            prev_state,
            outcome,
            prev_bound_counts,
            counts,
        ) for prev, prev_state, prev_bound_counts in zip(
            self._prevs, prev_states, self._split_bound_counts(*bound_counts))))

        count = reduce(self.merge_counts, prev_counts)
        count = max(count, 0)
        return prev_states, count

    def _order(self) -> Order:
        return Order.merge(*(prev._order() for prev in self._prevs))

    @cached_property
    def _cached_arity(self) -> int:
        return max(prev._arity() for prev in self._prevs)

    def _arity(self) -> int:
        return self._cached_arity

    @cached_property
    def _cached_bound_generators(
            self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return reduce(operator.add,
                      (prev._bound_generators() for prev in self._prevs))

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._cached_bound_generators

    def _split_bound_counts(self,
                            *bound_counts: int) -> 'Iterable[tuple[int, ...]]':
        """Splits a tuple of counts into one set of bound counts per expression."""
        index = 0
        for prev in self._prevs:
            counts_length = len(prev._bound_generators())
            yield bound_counts[index:index + counts_length]
            index += counts_length

    def __str__(self) -> str:
        return '(' + (' ' + self.symbol() + ' ').join(
            str(prev) for prev in self._prevs) + ')'


class IntersectionExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return min(left, right)

    @staticmethod
    def symbol() -> str:
        return '&'


class DifferenceExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left - right

    @staticmethod
    def symbol() -> str:
        return '-'


class UnionExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return max(left, right)

    @staticmethod
    def symbol() -> str:
        return '|'


class DisjointUnionExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left + right

    @staticmethod
    def symbol() -> str:
        return '+'


class SymmetricDifferenceExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return abs(max(left, 0) - max(right, 0))

    @staticmethod
    def symbol() -> str:
        return '^'
