__docformat__ = 'google'

from typing import Hashable
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

    def next_state(self, state, outcome: Outcome,
                   *counts: int) -> tuple[Hashable, int]:
        left_state, right_state = state or (None, None)
        left_state, left_count = self._left.next_state(left_state, outcome,
                                                       *counts)
        right_state, right_count = self._right.next_state(
            right_state, outcome, *counts)
        count = self.merge_counts(left_count, right_count)
        return (left_state, right_state), count

    def order(self) -> Order:
        return Order.merge(self._left.order(), self._right.order())

    def shift_variables(self, shift: int) -> MultisetExpression:
        return self.__class__(self._left.shift_variables(shift),
                              self._right.shift_variables(shift))

    @property
    def arity(self) -> int:
        return max(self._left.arity, self._right.arity)

    @cached_property
    def _key_tuple(self) -> tuple[Hashable, ...]:
        return type(self), self._left, self._right


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
