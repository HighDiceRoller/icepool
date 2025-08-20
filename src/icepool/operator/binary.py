__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator

from abc import abstractmethod
from functools import reduce

from typing import Iterator, MutableSequence, Sequence
from icepool.typing import T


class MultisetBinaryOperator(MultisetOperator[T]):

    def __init__(self, *children: MultisetExpression[T]) -> None:
        """Constructor.

        Args:
            *children: Any number of expressions to feed into the operator.
                If zero expressions are provided, the result will have all zero
                counts.
                If more than two expressions are provided, the counts will be
                `reduce`d.
        """
        self._children = children

    @staticmethod
    @abstractmethod
    def merge_counts(left: int, right: int) -> int:
        """Merge counts produced by the left and right expression."""

    @staticmethod
    @abstractmethod
    def symbol() -> str:
        """A symbol representing this operation."""

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        count = reduce(self.merge_counts, child_counts)
        return None, count

    @property
    def _expression_key(self):
        return type(self)

    def __str__(self) -> str:
        return '(' + (' ' + self.symbol() + ' ').join(
            str(child) for child in self._children) + ')'


class MultisetIntersection(MultisetBinaryOperator):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return min(left, right)

    @staticmethod
    def symbol() -> str:
        return '&'


class MultisetDifferenceDropNegative(MultisetBinaryOperator):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return max(left - right, 0)

    @staticmethod
    def symbol() -> str:
        return '-'


class MultisetDifferenceKeepNegative(MultisetBinaryOperator):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left - right

    @staticmethod
    def symbol() -> str:
        return '-'


class MultisetUnion(MultisetBinaryOperator):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return max(left, right)

    @staticmethod
    def symbol() -> str:
        return '|'


class MultisetAdditiveUnion(MultisetBinaryOperator):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left + right

    @staticmethod
    def symbol() -> str:
        return '+'

    def _initial_state(self, order, outcomes, child_sizes: Sequence,
                       source_sizes: Iterator, arg_sizes: Sequence):
        left_size, right_size = child_sizes
        if left_size is None or right_size is None:
            return None, None
        else:
            return None, child_sizes[0] + child_sizes[1]


class MultisetSymmetricDifference(MultisetBinaryOperator):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return abs(left - right)

    @staticmethod
    def symbol() -> str:
        return '^'
