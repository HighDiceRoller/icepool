__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

from functools import cached_property

from icepool.typing import Order, T_contra
from types import EllipsisType
from typing import Hashable, Sequence


class KeepExpression(MultisetExpression[T_contra]):
    """An expression to keep some of the lowest or highest elements of a multiset."""

    _keep_order: Order
    _keep_tuple: tuple[int, ...]
    """The left side is always the end regardless of order."""
    _drop: int | None
    """If set, this is a slice [a:] or [:-b], and _keep_tuple is unused."""

    # May return child unmodified.
    def __new__(  # type: ignore
        cls, child: MultisetExpression[T_contra], /, *,
        index: slice | Sequence[int | EllipsisType]
    ) -> MultisetExpression[T_contra]:
        cls._validate_output_arity(child)
        self = super(KeepExpression, cls).__new__(cls)
        self._children = (child, )
        if isinstance(index, slice):
            if index.step is not None:
                raise ValueError('step is not supported.')
            start, stop = index.start, index.stop
            if start is None:
                if stop is None:
                    # [:] returns child as-is.
                    return child
                else:
                    if stop >= 0:
                        # [:+b] keeps from the bottom.
                        self._keep_order = Order.Ascending
                        self._keep_tuple = (1, ) * stop
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
                        self._keep_tuple = (1, ) * -start
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
                        self._keep_tuple = (0, ) * start + (1, ) * (stop -
                                                                    start)
                        self._drop = None
                    elif start < 0 and stop < 0:
                        # [-a:-b]
                        self._keep_order = Order.Descending
                        self._keep_tuple = (0, ) * -stop + (1, ) * (stop -
                                                                    start)
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
    def _new_raw(cls, child: MultisetExpression[T_contra], /, *,
                 keep_order: Order, keep_tuple: tuple[int,
                                                      ...], drop: int | None):
        self = super(KeepExpression, cls).__new__(cls)
        self._children = (child, )
        self._keep_order = keep_order
        self._keep_tuple = keep_tuple
        self._drop = drop
        return self

    def _make_unbound(self, *unbound_children) -> 'icepool.MultisetExpression':
        return KeepExpression._new_raw(*unbound_children,
                                       keep_order=self._keep_order,
                                       keep_tuple=self._keep_tuple,
                                       drop=self._drop)

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:
        child = self._children[0]
        if self._drop is None:
            # Use _keep_tuple.
            remaining, child_state = state or (self._keep_tuple, None)
            child_state, count = child._next_state(child_state, outcome,
                                                   *counts)
            if count < 0:
                raise RuntimeError(
                    'KeepExpression is not compatible with incoming negative counts.'
                )
            keep = sum(remaining[:count])
            remaining = remaining[count:]
            return (remaining, child_state), keep
        else:
            # Use drop.
            remaining, child_state = state or (self._drop, None)
            child_state, count = child._next_state(child_state, outcome,
                                                   *counts)
            if count < 0:
                raise RuntimeError(
                    'KeepExpression is not compatible with incoming negative counts.'
                )
            dropped = min(remaining, count)
            count -= dropped
            remaining -= dropped
            return (remaining, child_state), count

    def order(self) -> Order:
        return Order.merge(self._keep_order, self._children[0].order())

    def _free_arity(self) -> int:
        return self._children[0]._free_arity()

    def __str__(self) -> str:
        child = self._children[0]
        if self._drop:
            if self.order == Order.Ascending:
                return f'{child}[{self._drop}:]'
            else:
                return f'{child}[:-{self._drop}]'
        else:
            index_string = ', '.join(str(x) for x in self._keep_tuple)
            if self.order == Order.Ascending:
                index_string = index_string + ', ...'
            else:
                index_string = '..., ' + index_string
            return f'{child}[{index_string}]'
