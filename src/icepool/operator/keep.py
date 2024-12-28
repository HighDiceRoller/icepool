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


class MultisetKeep(MultisetOperator[T]):
    """An expression to keep some of the lowest or highest elements of a multiset."""

    _keep_order: Order
    _keep_tuple: tuple[int, ...]
    """The left side is always the end regardless of order."""
    _drop: int | None
    """If set, this is a slice [a:] or [:-b], and _keep_tuple is unused."""

    # May return child unmodified.
    def __new__(  # type: ignore
            cls, child: MultisetExpression[T], /, *, index: slice
        | Sequence[int | EllipsisType]) -> MultisetExpression[T]:
        self = super(MultisetKeep, cls).__new__(cls)
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
    def _new_raw(cls, child: MultisetExpression[T], /, *, keep_order: Order,
                 keep_tuple: tuple[int, ...], drop: int | None):
        self = super(MultisetKeep, cls).__new__(cls)
        self._children = (child, )
        self._keep_order = keep_order
        self._keep_tuple = keep_tuple
        self._drop = drop
        return self

    def _copy(
        self, new_children: 'tuple[MultisetExpression[T], ...]'
    ) -> 'MultisetExpression[T]':
        return MultisetKeep._new_raw(new_children[0],
                                     keep_order=self._keep_order,
                                     keep_tuple=self._keep_tuple,
                                     drop=self._drop)

    def _transform_next(
            self, new_children: 'tuple[MultisetExpression[T], ...]',
            outcome: T,
            counts: 'tuple[int, ...]') -> 'tuple[MultisetExpression[T], int]':
        child_count = max(counts[0], 0)

        if self._drop is None:
            # Use keep_tuple.
            count = sum(self._keep_tuple[:child_count])
            next_keep_tuple = self._keep_tuple[child_count:]
            return MultisetKeep._new_raw(new_children[0],
                                         keep_order=self._keep_order,
                                         keep_tuple=next_keep_tuple,
                                         drop=None), count
        else:
            # Use drop.
            dropped = min(self._drop, child_count)
            count = child_count - dropped
            next_drop = self._drop - dropped
            return MultisetKeep._new_raw(new_children[0],
                                         keep_order=self._keep_order,
                                         keep_tuple=(),
                                         drop=next_drop), count

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return self._keep_order, OrderReason.Mandatory

    @property
    def _local_hash_key(self) -> Hashable:
        return self._keep_order, self._keep_tuple, self._drop

    def __str__(self) -> str:
        child = self._children[0]
        if self._drop:
            if self._keep_order == Order.Ascending:
                return f'{child}[{self._drop}:]'
            else:
                return f'{child}[:-{self._drop}]'
        else:
            index_string = ', '.join(str(x) for x in self._keep_tuple)
            if self._keep_order == Order.Ascending:
                index_string = index_string + ', ...'
            else:
                index_string = '..., ' + index_string
            return f'{child}[{index_string}]'
