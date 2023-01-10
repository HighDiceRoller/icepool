__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Outcome

from abc import abstractmethod
from functools import cached_property


class BinaryOperatorExpression(MultisetExpression):

    def __init__(self, left: MultisetExpression,
                 right: MultisetExpression) -> None:
        self._left = left
        self._right = right

    def __eq__(self, other) -> bool:
        if type(self) == type(other):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _key_tuple(self) -> tuple:
        return type(self), self._left, self._right

    def __hash__(self) -> int:
        return hash(self._key_tuple)

    @staticmethod
    @abstractmethod
    def merge_counts(left: int, right: int) -> int:
        """Merge counts produced by the left and right expression."""

    def evaluate(self, outcome: Outcome, *counts: int) -> int:
        left = self._left.evaluate(outcome, *counts)
        right = self._right.evaluate(outcome, *counts)
        return self.merge_counts(left, right)


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
