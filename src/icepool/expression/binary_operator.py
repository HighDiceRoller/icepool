__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

import operator
from abc import abstractmethod
from functools import cached_property, reduce

from typing import Hashable, Iterable, Sequence
from icepool.typing import Order, Outcome, T_contra


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
        inner_states = state or (None,) * len(self._inners)

        inner_states, inner_counts = zip(
            *(inner._next_state(inner_state, outcome, *counts)
              for inner, inner_state in zip(self._inners, inner_states)))

        count = reduce(self.merge_counts, inner_counts)
        count = max(count, 0)
        return inner_states, count

    def _order(self) -> Order:
        return Order.merge(*(inner._order() for inner in self._inners))

    @cached_property
    def _cached_arity(self) -> int:
        return max(inner._free_arity() for inner in self._inners)

    def _free_arity(self) -> int:
        return self._cached_arity

    @cached_property
    def _cached_bound_generators(
            self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return reduce(operator.add,
                      (inner._bound_generators() for inner in self._inners))

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._cached_bound_generators

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_inners = []
        for inner in self._inners:
            unbound_inner, prefix_start = inner._unbind(prefix_start,
                                                        free_start)
            unbound_inners.append(unbound_inner)
        unbound_expression = type(self)(*unbound_inners)
        return unbound_expression, prefix_start

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
