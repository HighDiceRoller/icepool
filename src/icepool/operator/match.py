__docformat__ = 'google'

import icepool

from icepool.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator
from icepool.order import Order, OrderReason

import operator
from abc import abstractmethod
from functools import cached_property, reduce

from types import EllipsisType
from typing import Callable, Collection, Hashable, Iterable, Sequence
from icepool.typing import T


class MultisetSortMatch(MultisetOperator[T]):

    def __init__(self,
                 left: MultisetExpression[T],
                 right: MultisetExpression[T],
                 *,
                 order: Order,
                 tie: int,
                 left_first: int,
                 right_first: int,
                 left_lead: int = 0):
        if order == Order.Any:
            order = Order.Descending
        self._children = (left, right)
        self._order = order
        self._tie = tie
        self._left_first = left_first
        self._right_first = right_first
        self._left_lead = left_lead

    def _copy(
        self, new_children: 'tuple[MultisetExpression[T], ...]'
    ) -> 'MultisetExpression[T]':
        return MultisetSortMatch(*new_children,
                                 order=self._order,
                                 tie=self._tie,
                                 left_first=self._left_first,
                                 right_first=self._right_first,
                                 left_lead=self._left_lead)

    def _transform_next(
            self, new_children: 'tuple[MultisetExpression[T], ...]',
            outcome: T,
            counts: 'tuple[int, ...]') -> 'tuple[MultisetExpression[T], int]':
        left_count, right_count = counts
        left_count = max(left_count, 0)
        right_count = max(right_count, 0)

        count = 0

        if self._left_lead >= 0:
            count += max(min(right_count - self._left_lead, left_count),
                         0) * self._tie
        elif self._left_lead < 0:
            count += max(min(left_count + self._left_lead, right_count),
                         0) * self._tie
            count += min(-self._left_lead, left_count) * self._right_first

        next_left_lead = self._left_lead + left_count - right_count

        if next_left_lead > 0:
            count += min(next_left_lead, left_count) * self._left_first

        return MultisetSortMatch(*new_children,
                                 order=self._order,
                                 tie=self._tie,
                                 left_first=self._left_first,
                                 right_first=self._right_first,
                                 left_lead=next_left_lead), count

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return self._order, OrderReason.Mandatory

    @property
    def _local_hash_key(self) -> Hashable:
        return (MultisetSortMatch, self._order, self._tie, self._left_first,
                self._right_first, self._left_lead)


class MultisetMaximumMatch(MultisetOperator[T]):

    def __init__(self,
                 left: MultisetExpression[T],
                 right: MultisetExpression[T],
                 *,
                 order: Order,
                 match_equal: bool,
                 keep: bool,
                 prev_matchable=0):
        self._children = (left, right)
        self._order = order
        self._match_equal = match_equal
        self._keep = keep
        self._prev_matchable = prev_matchable

    def _copy(
        self, new_children: 'tuple[MultisetExpression[T], ...]'
    ) -> 'MultisetExpression[T]':
        return MultisetMaximumMatch(*new_children,
                                    order=self._order,
                                    match_equal=self._match_equal,
                                    keep=self._keep,
                                    prev_matchable=self._prev_matchable)

    def _transform_next(
            self, new_children: 'tuple[MultisetExpression[T], ...]',
            outcome: T,
            counts: 'tuple[int, ...]') -> 'tuple[MultisetExpression[T], int]':
        left_count, right_count = counts
        left_count = max(left_count, 0)
        right_count = max(right_count, 0)

        if self._match_equal:
            new_matches = min(self._prev_matchable + right_count, left_count)
        else:
            new_matches = min(self._prev_matchable, left_count)
        next_prev_matchable = self._prev_matchable + right_count - new_matches
        if self._keep:
            count = new_matches
        else:
            count = left_count - new_matches
        return MultisetMaximumMatch(*new_children,
                                    order=self._order,
                                    match_equal=self._match_equal,
                                    keep=self._keep,
                                    prev_matchable=next_prev_matchable), count

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return self._order, OrderReason.Mandatory

    @property
    def _local_hash_key(self) -> Hashable:
        return (MultisetMaximumMatch, self._order, self._match_equal,
                self._keep, self._prev_matchable)
