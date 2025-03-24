__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator
from icepool.order import Order, OrderReason, UnsupportedOrderError

import operator
from abc import abstractmethod
from functools import cached_property, reduce

from types import EllipsisType
from typing import Callable, Collection, Hashable, Iterable, Sequence
from icepool.typing import T


class MultisetSortMatch(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *, order: Order, tie: int,
                 left_first: int, right_first: int):
        if order == Order.Any:
            order = Order.Descending
        self._children = (left, right)
        self._order = order
        self._tie = tie
        self._left_first = left_first
        self._right_first = right_first

    def _initial_state(self, order, outcomes) -> int:
        """
        
        Returns:
            left_lead: The number of elements by which the left operand is
                ahead.
        """
        if order != self._order:
            raise UnsupportedOrderError()
        return 0

    def _next_state(self, left_lead, order, outcome, child_counts,
                    source_counts, param_counts):
        left_count, right_count = child_counts
        left_count = max(left_count, 0)
        right_count = max(right_count, 0)

        count = 0
        if left_lead >= 0:
            count += max(min(right_count - left_lead, left_count),
                         0) * self._tie
        elif left_lead < 0:
            count += max(min(left_count + left_lead, right_count),
                         0) * self._tie
            count += min(-left_lead, left_count) * self._right_first

        left_lead += left_count - right_count

        if left_lead > 0:
            count += min(left_lead, left_count) * self._left_first

        return left_lead, count

    @property
    def _expression_key(self):
        return MultisetSortMatch, self._order, self._tie, self._left_first, self._right_first


class MultisetMaximumMatch(MultisetOperator[T]):

    def __init__(self, left: MultisetExpression[T],
                 right: MultisetExpression[T], *, order: Order,
                 match_equal: bool, keep: bool):
        self._children = (left, right)
        self._order = order
        self._match_equal = match_equal
        self._keep = keep

    def _initial_state(self, order, outcomes):
        """
        
        Returns:
            prev_matchable: The number of previously-seen elements that are
                eligible to be matched.
        """
        if order != self._order:
            raise UnsupportedOrderError()
        return 0

    def _next_state(self, prev_matchable, order, outcome, child_counts,
                    source_counts, param_counts):
        left_count, right_count = child_counts
        left_count = max(left_count, 0)
        right_count = max(right_count, 0)

        if self._match_equal:
            new_matches = min(prev_matchable + right_count, left_count)
        else:
            new_matches = min(prev_matchable, left_count)
        prev_matchable += right_count - new_matches
        if self._keep:
            count = new_matches
        else:
            count = left_count - new_matches
        return prev_matchable, count

    @property
    def _expression_key(self):
        return MultisetMaximumMatch, self._order, self._match_equal, self._keep
