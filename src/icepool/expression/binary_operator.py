__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

import operator
from abc import abstractmethod
from functools import cached_property, reduce

from typing import Hashable
from icepool.typing import Order, T


class BinaryOperatorExpression(MultisetExpression[T]):

    def __init__(self, *children: MultisetExpression[T]) -> None:
        """Constructor.

        Args:
            *children: Any number of expressions to feed into the operator.
                If zero expressions are provided, the result will have all zero
                counts.
                If more than two expressions are provided, the counts will be
                `reduce`d.
        """
        for child in children:
            self._validate_output_arity(child)
        self._children = children

    def _make_unbound(self, *unbound_children) -> 'icepool.MultisetExpression':
        return type(self)(*unbound_children)

    @staticmethod
    @abstractmethod
    def merge_counts(left: int, right: int) -> int:
        """Merge counts produced by the left and right expression."""

    @staticmethod
    @abstractmethod
    def symbol() -> str:
        """A symbol representing this operation."""

    def _next_state(self, state, outcome: T, *counts:
                    int) -> tuple[Hashable, int]:
        if len(self._children) == 0:
            return (), 0
        child_states = state or (None, ) * len(self._children)

        child_states, child_counts = zip(
            *(child._next_state(child_state, outcome, *counts)
              for child, child_state in zip(self._children, child_states)))

        count = reduce(self.merge_counts, child_counts)
        return child_states, count

    def order(self) -> Order:
        return Order.merge(*(child.order() for child in self._children))

    @cached_property
    def _cached_arity(self) -> int:
        return max(child._free_arity() for child in self._children)

    def _free_arity(self) -> int:
        return self._cached_arity

    def __str__(self) -> str:
        return '(' + (' ' + self.symbol() + ' ').join(
            str(child) for child in self._children) + ')'


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
