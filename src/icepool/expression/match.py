__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

from functools import cached_property

from typing import Hashable
from icepool.typing import Order, T_contra


class SortMatchExpression(MultisetExpression[T_contra]):

    def __init__(self, left: MultisetExpression[T_contra],
                 right: MultisetExpression[T_contra], *, order: Order,
                 tie: int, left_first: int, right_first: int):
        if order == Order.Any:
            order = Order.Descending
        self._left = left
        self._right = right
        self._inners = (left, right)
        self._order = order
        self._tie = tie
        self._left_first = left_first
        self._right_first = right_first

    def _make_unbound(self, *unbound_inners) -> 'icepool.MultisetExpression':
        return SortMatchExpression(*unbound_inners,
                                   order=self._order,
                                   tie=self._tie,
                                   left_first=self._left_first,
                                   right_first=self._right_first)

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:
        left_state, right_state, left_lead = state or (None, None, 0)
        left_state, left_count = self._left._next_state(
            state, outcome, *counts)
        right_state, right_count = self._right._next_state(
            state, outcome, *counts)

        if left_count < 0 or right_count < 0:
            raise RuntimeError(
                'SortMatchedExpression does not support negative counts.')

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

        return (left_state, right_state, left_lead), count

    def order(self) -> Order:
        return Order.merge(self._order, self._left.order(),
                           self._right.order())

    def _free_arity(self) -> int:
        return max(self._left._free_arity(), self._right._free_arity())


class MaximumMatchExpression(MultisetExpression[T_contra]):

    def __init__(self, left: MultisetExpression[T_contra],
                 right: MultisetExpression[T_contra], *, order: Order,
                 match_equal: bool, keep: bool):
        self._left = left
        self._right = right
        self._inners = (left, right)
        self._order = order
        self._match_equal = match_equal
        self._keep = keep

    def _make_unbound(self, *unbound_inners) -> 'icepool.MultisetExpression':
        return MaximumMatchExpression(*unbound_inners,
                                      order=self._order,
                                      match_equal=self._match_equal,
                                      keep=self._keep)

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:
        left_state, right_state, prev_matchable = state or (None, None, 0)
        left_state, left_count = self._left._next_state(
            state, outcome, *counts)
        right_state, right_count = self._right._next_state(
            state, outcome, *counts)

        if left_count < 0 or right_count < 0:
            raise RuntimeError(
                'MaximumMatchedExpression does not support negative counts.')

        if self._match_equal:
            new_matches = min(prev_matchable + right_count, left_count)
        else:
            new_matches = min(prev_matchable, left_count)
        prev_matchable += right_count - new_matches
        if self._keep:
            count = new_matches
        else:
            count = left_count - new_matches
        return (left_state, right_state, prev_matchable), count

    def order(self) -> Order:
        return Order.merge(self._order, self._left.order(),
                           self._right.order())

    def _free_arity(self) -> int:
        return max(self._left._free_arity(), self._right._free_arity())
