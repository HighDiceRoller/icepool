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


class MultisetKeep(MultisetOperator[T]):
    """An expression to keep some of the lowest or highest elements of a multiset."""

    def __init__(  # type: ignore
        self, child: MultisetExpression[T], /, *,
        index: 'slice | Sequence[int | EllipsisType]'
    ) -> MultisetExpression[T]:
        self._children = (child, )
        self._index = index

    def _initial_state(self, order, outcomes) -> tuple[tuple[int, ...], bool]:
        """
        
        Returns:
            * A keep_tuple that pops from the left regardless of order.
            * Whether items are kept after running out of the keep_tuple
        """
        if isinstance(self._index, slice):
            if self._index.step is not None:
                raise ValueError('step is not supported.')
            start, stop = self._index.start, self._index.stop
            if start is None:
                if stop is None:
                    return (), True
                else:
                    if stop >= 0:
                        # [:+b] keeps from the bottom.
                        if order != Order.Ascending:
                            raise UnsupportedOrderError()
                        return (1, ) * stop, False
                    else:
                        # [:-b] drops from the top.
                        if order != Order.Descending:
                            raise UnsupportedOrderError()
                        return (0, ) * -stop, True
            else:
                # start is not None.
                if stop is None:
                    if start < 0:
                        # [-a:] keeps from the top.
                        if order != Order.Descending:
                            raise UnsupportedOrderError()
                        return (1, ) * -start, False
                    else:
                        # [a:] drops from the bottom.
                        if order != Order.Ascending:
                            raise UnsupportedOrderError()
                        return (0, ) * start, True
                else:
                    # Both are provided.
                    if start >= 0 and stop >= 0:
                        # [a:b]
                        if order != Order.Ascending:
                            raise UnsupportedOrderError()
                        return (0, ) * start + (1, ) * (stop - start), False
                    elif start < 0 and stop < 0:
                        # [-a:-b]
                        if order != Order.Descending:
                            raise UnsupportedOrderError()
                        return (0, ) * -stop + (1, ) * (stop - start), False
                    else:
                        raise ValueError(
                            'If both start and stop are provided, they must be both negative or both non-negative.'
                        )
        elif isinstance(self._index, Sequence):
            if self._index[0] == ...:
                if order != Order.Descending:
                    raise UnsupportedOrderError()
                # Type verified below.
                result = tuple(reversed(self._index[1:]))
            elif self._index[-1] == ...:
                if order != Order.Ascending:
                    raise UnsupportedOrderError()
                # Type verified below.
                result = tuple(self._index[:-1])
            else:
                raise ValueError(
                    'If a sequence is provided, either the first or last element (but not both) must be an Ellipsis (...)'
                )
            if ... in result:
                raise ValueError(
                    'If a sequence is provided, either the first or last element (but not both) must be an Ellipsis (...)'
                )
            return result, False  # type: ignore
        else:
            raise TypeError(f'Invalid type {type(self._index)} for index.')

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    param_counts):
        keep_tuple, keep_overrun = state
        child_count = max(child_counts[0], 0)
        count = sum(keep_tuple[:child_count])
        if keep_overrun:
            count += max(child_count - len(keep_tuple), 0)
        keep_tuple = keep_tuple[child_count:]
        return (keep_tuple, keep_overrun), count

    @property
    def _expression_key(self):
        return MultisetKeep, self._index

    @property
    def _dungeonlet_key(self):
        return MultisetKeep

    def __str__(self) -> str:
        child = self._children[0]
        return f'{child}[{self._index}]'
