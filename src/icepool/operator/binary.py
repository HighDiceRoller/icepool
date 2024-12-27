__docformat__ = 'google'

import icepool

from icepool.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator
from icepool.order import Order, OrderReason

import operator
from abc import abstractmethod
from functools import cached_property, reduce

from typing import Hashable, Iterable
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

    def _copy(
        self, new_children: 'tuple[MultisetExpression[T], ...]'
    ) -> 'MultisetExpression[T]':
        return type(self)(*new_children)

    def _transform_next(
            self, new_children: 'tuple[MultisetExpression[T], ...]',
            outcome: T,
            counts: 'tuple[int, ...]') -> 'tuple[MultisetExpression[T], int]':
        count = reduce(self.merge_counts, counts)
        return type(self)(*new_children), count

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    @property
    def _local_hash_key(self) -> Hashable:
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


class MultisetDifference(MultisetBinaryOperator):

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


class MultisetSymmetricDifference(MultisetBinaryOperator):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return abs(left - right)

    @staticmethod
    def symbol() -> str:
        return '^'
