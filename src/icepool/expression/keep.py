__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

from functools import cached_property

from icepool.typing import Order, T_contra
from types import EllipsisType
from typing import Hashable, Sequence


class KeepExpression(MultisetExpression[T_contra]):
    """An expression to keep some of the lowest or highest elements of a multiset."""

    _inner: MultisetExpression[T_contra]
    _keep_order: Order
    _keep_tuple: tuple[int, ...]
    """The left side is always the end regardless of order."""
    _drop: int | None
    """If set, this is a slice [a:] or [:-b], and _keep_tuple is unused."""

    # May return inner unmodified.
    def __new__(  # type: ignore
        cls, inner: MultisetExpression[T_contra],
        index: slice | Sequence[int | EllipsisType]
    ) -> MultisetExpression[T_contra]:
        cls._validate_output_arity(inner)
        self = super(KeepExpression, cls).__new__(cls)
        self._inner = inner
        if isinstance(index, slice):
            if index.step is not None:
                raise ValueError('step is not supported.')
            start, stop = index.start, index.stop
            if start is None:
                if stop is None:
                    # [:] returns inner as-is.
                    return inner
                else:
                    if stop >= 0:
                        # [:+b] keeps from the bottom.
                        self._keep_order = Order.Ascending
                        self._keep_tuple = (1,) * stop
                        self._drop = None
                    else:
                        # [:-b] drops from the top.
                        self._keep_order = Order.Descending
                        self._keep_tuple = ()
                        self._drop = -stop
            else:
                # start is not None.
                if stop is None:
                    if start < 0:
                        # [-a:] keeps from the top.
                        self._keep_order = Order.Descending
                        self._keep_tuple = (1,) * -start
                        self._drop = None
                    else:
                        # [a:] drops from the bottom.
                        self._keep_order = Order.Ascending
                        self._keep_tuple = ()
                        self._drop = start
                else:
                    # Both are provided.
                    if start >= 0 and stop >= 0:
                        # [a:b]
                        self._keep_order = Order.Ascending
                        self._keep_tuple = (0,) * start + (1,) * (stop - start)
                        self._drop = None
                    elif start < 0 and stop < 0:
                        # [-a:-b]
                        self._keep_order = Order.Descending
                        self._keep_tuple = (0,) * -stop + (1,) * (stop - start)
                        self._drop = None
                    else:
                        raise ValueError(
                            'If both start and stop are provided, they must be both negative or both non-negative.'
                        )
        elif isinstance(index, Sequence):
            if index[0] == ...:
                self._keep_order = Order.Descending
                # Type verified below.
                self._keep_tuple = tuple(reversed(index[1:]))  # type: ignore
                self._drop = None
            elif index[-1] == ...:
                self._keep_order = Order.Ascending
                # Type verified below.
                self._keep_tuple = tuple(index[:-1])  # type: ignore
                self._drop = None
            else:
                raise ValueError(
                    'If a sequence is provided, either the first or last element (but not both) must be an Ellipsis (...)'
                )
            if ... in self._keep_tuple:
                raise ValueError(
                    'If a sequence is provided, either the first or last element (but not both) must be an Ellipsis (...)'
                )
        else:
            raise TypeError(f'Invalid type {type(index)} for index.')
        return self

    @classmethod
    def _new_raw(cls, inner: MultisetExpression[T_contra], keep_order: Order,
                 keep_tuple: tuple[int, ...], drop: int | None):
        self = super(KeepExpression, cls).__new__(cls)
        self._inner = inner
        self._keep_order = keep_order
        self._keep_tuple = keep_tuple
        self._drop = drop
        return self

    def _next_state(self, state, outcome: T_contra,
                    *counts: int) -> tuple[Hashable, int]:
        if self._drop is None:
            # Use _keep_tuple.
            remaining, inner_state = state or (self._keep_tuple, None)
            inner_state, count = self._inner._next_state(
                inner_state, outcome, *counts)
            if count < 0:
                raise RuntimeError(
                    'KeepExpression is not compatible with incoming negative counts.'
                )
            keep = sum(remaining[:count])
            remaining = remaining[count:]
            return (remaining, inner_state), keep
        else:
            # Use drop.
            remaining, inner_state = state or (self._drop, None)
            inner_state, count = self._inner._next_state(
                inner_state, outcome, *counts)
            if count < 0:
                raise RuntimeError(
                    'KeepExpression is not compatible with incoming negative counts.'
                )
            dropped = min(remaining, count)
            count -= dropped
            remaining -= dropped
            return (remaining, inner_state), count

    def _order(self) -> Order:
        return Order.merge(self._keep_order, self._inner._order())

    @cached_property
    def _cached_bound_generators(
            self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._inner._bound_generators()

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._cached_bound_generators

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_inner, prefix_start = self._inner._unbind(
            prefix_start, free_start)
        unbound_expression = KeepExpression._new_raw(unbound_inner,
                                                     self._keep_order,
                                                     self._keep_tuple,
                                                     self._drop)
        return unbound_expression, prefix_start

    def _free_arity(self) -> int:
        return self._inner._free_arity()

    def __str__(self) -> str:
        if self._drop:
            if self._order == Order.Ascending:
                return f'{self._inner}[{self._drop}:]'
            else:
                return f'{self._inner}[:-{self._drop}]'
        else:
            index_string = ', '.join(str(x) for x in self._keep_tuple)
            if self._order == Order.Ascending:
                index_string = index_string + ', ...'
            else:
                index_string = '..., ' + index_string
            return f'{self._inner}[{index_string}]'