__docformat__ = 'google'

from typing import Hashable
from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Outcome

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

    def evaluate_counts(self, outcome: Outcome, *counts: int) -> int:
        left = self._left.evaluate_counts(outcome, *counts)
        right = self._right.evaluate_counts(outcome, *counts)
        result = self.merge_counts(left, right)
        return max(result, 0)

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


class DifferenceExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left - right


class UnionExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return max(left, right)


class DisjointUnionExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left + right


class SymmetricDifferenceExpression(BinaryOperatorExpression):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return abs(max(left, 0) - max(right, 0))
