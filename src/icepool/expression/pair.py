__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

from functools import cached_property

from typing import Hashable
from icepool.typing import Order, T_contra


class PairKeepExpression(MultisetExpression[T_contra]):

    def __init__(self, source: MultisetExpression[T_contra],
                 other: MultisetExpression[T_contra], *, order: Order,
                 allow_equal: bool, keep: bool):
        self._source = source
        self._other = other
        self._order = order
        self._allow_equal = allow_equal
        self._keep = keep

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:
        source_state, other_state, pairable = state or (None, None, 0)
        source_state, source_count = self._source._next_state(
            state, outcome, *counts)
        other_state, other_count = self._other._next_state(
            state, outcome, *counts)
        if self._allow_equal:
            new_pairs = min(pairable + other_count, source_count)
        else:
            new_pairs = min(pairable, source_count)
        pairable += other_count - new_pairs
        if self._keep:
            count = new_pairs
        else:
            count = source_count - new_pairs
        return (source_state, other_state, pairable), count

    def order(self) -> Order:
        return Order.merge(self._order, self._source.order(),
                           self._other.order())

    @cached_property
    def _cached_bound_generators(
            self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._source._bound_generators(
        ) + self._other._bound_generators()

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._cached_bound_generators

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_source, prefix_start = self._source._unbind(
            prefix_start, free_start)
        unbound_other, prefix_start = self._other._unbind(
            prefix_start, free_start)
        unbound_expression: MultisetExpression = PairKeepExpression(
            unbound_source,
            unbound_other,
            order=self._order,
            allow_equal=self._allow_equal,
            keep=self._keep)
        return unbound_expression, prefix_start

    def _free_arity(self) -> int:
        return max(self._source._free_arity(), self._other._free_arity())
