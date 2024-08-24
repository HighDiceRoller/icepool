__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

import operator
from abc import abstractmethod
from functools import cached_property, reduce

from typing import Hashable
from icepool.typing import Order, T_contra


class BinaryOperatorExpression(MultisetExpression[T_contra]):

    def __init__(self, *inners: MultisetExpression[T_contra]) -> None:
        """Constructor.

        Args:
            *inners: Any number of expressions to feed into the operator.
                If zero expressions are provided, the result will have all zero
                counts.
                If more than two expressions are provided, the counts will be
                `reduce`d.
        """
        for inner in inners:
            self._validate_output_arity(inner)
        self._inners = inners

    def _make_unbound(self, *unbound_inners) -> 'icepool.MultisetExpression':
        return type(self)(*unbound_inners)

    @staticmethod
    @abstractmethod
    def merge_counts(left: int, right: int) -> int:
        """Merge counts produced by the left and right expression."""

    @staticmethod
    @abstractmethod
    def symbol() -> str:
        """A symbol representing this operation."""

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:
        if len(self._inners) == 0:
            return (), 0
        inner_states = state or (None, ) * len(self._inners)

        inner_states, inner_counts = zip(
            *(inner._next_state(inner_state, outcome, *counts)
              for inner, inner_state in zip(self._inners, inner_states)))

        count = reduce(self.merge_counts, inner_counts)
        return inner_states, count

    def order(self) -> Order:
        return Order.merge(*(inner.order() for inner in self._inners))

    @cached_property
    def _cached_arity(self) -> int:
        return max(inner._free_arity() for inner in self._inners)

    def _free_arity(self) -> int:
        return self._cached_arity

    def __str__(self) -> str:
        return '(' + (' ' + self.symbol() + ' ').join(
            str(inner) for inner in self._inners) + ')'


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


class AdditiveUnionExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left + right

    @staticmethod
    def symbol() -> str:
        return '+'


class SymmetricDifferenceExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return abs(left - right)

    @staticmethod
    def symbol() -> str:
        return '^'
