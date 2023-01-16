__docformat__ = 'google'

import icepool

from typing import Hashable, Sequence
from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Order, Outcome

from abc import abstractmethod
from functools import cached_property


class BinaryOperatorExpression(MultisetExpression):

    def __init__(self, left: MultisetExpression,
                 right: MultisetExpression) -> None:
        self._left = left
        self._right = right

    @staticmethod
    @abstractmethod
    def merge_counts(left: int, right: int) -> int:
        """Merge counts produced by the left and right expression."""

    def next_state(self, state, outcome: Outcome, bound_counts: tuple[int, ...],
                   counts: tuple[int, ...]) -> tuple[Hashable, int]:
        bound_counts_split = len(self._left.bound_generators())
        left_bound_counts = bound_counts[:bound_counts_split]
        right_bound_counts = bound_counts[bound_counts_split:]
        left_state, right_state = state or (None, None)
        left_state, left_count = self._left.next_state(left_state, outcome,
                                                       left_bound_counts,
                                                       counts)
        right_state, right_count = self._right.next_state(
            right_state, outcome, right_bound_counts, counts)
        count = self.merge_counts(left_count, right_count)
        count = max(count, 0)
        return (left_state, right_state), count

    def order(self) -> Order:
        return Order.merge(self._left.order(), self._right.order())

    @property
    def arity(self) -> int:
        return max(self._left.arity, self._right.arity)

    @cached_property
    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._left.bound_generators() + self._right.bound_generators()

    def bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._bound_generators


class IntersectionExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return min(left, right)

    def __str__(self) -> str:
        return f'({self._left} & {self._right})'


class DifferenceExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left - right

    def __str__(self) -> str:
        return f'({self._left} - {self._right})'


class UnionExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return max(left, right)

    def __str__(self) -> str:
        return f'({self._left} | {self._right})'


class DisjointUnionExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left + right

    def __str__(self) -> str:
        return f'({self._left} + {self._right})'


class SymmetricDifferenceExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return abs(max(left, 0) - max(right, 0))

    def __str__(self) -> str:
        return f'({self._left} ^ {self._right})'
