__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator
from icepool.order import Order, UnsupportedOrder

from types import EllipsisType
from typing import Iterator, MutableSequence, Sequence
from icepool.typing import T


class MultisetKeep(MultisetOperator[T]):
    """An expression to keep some of the lowest or highest elements of a multiset."""

    def __init__(  # type: ignore
        self, child: MultisetExpression[T], /, *,
        index: 'slice | Sequence[int | EllipsisType]'
    ) -> MultisetExpression[T]:
        self._children = (child, )
        self._index = index

    def _initial_state(
        self, order, outcomes, child_sizes: Sequence, source_sizes: Iterator,
        arg_sizes: Sequence
    ) -> tuple[tuple[tuple[int, ...], bool], int | None]:
        """
        
        Returns:
            * A keep_tuple that pops from the left regardless of order.
            * Whether items are kept after running out of the keep_tuple
        """
        child_size = child_sizes[0]
        keep_tuple: tuple[int, ...]
        keep_more: bool

        if isinstance(self._index, slice):
            if self._index.step is not None:
                raise ValueError('step is not supported.')
            start, stop = self._index.start, self._index.stop
            if start is None:
                if stop is None:
                    keep_tuple = ()
                    keep_more = True
                    required_order = Order.Any
                else:
                    if stop >= 0:
                        # [:+b] keeps from the bottom.
                        keep_tuple = (1, ) * stop
                        keep_more = False
                        required_order = Order.Ascending
                    else:
                        # [:-b] drops from the top.
                        keep_tuple = (0, ) * -stop
                        keep_more = True
                        required_order = Order.Descending
            else:
                # start is not None.
                if stop is None:
                    if start < 0:
                        # [-a:] keeps from the top.
                        keep_tuple = (1, ) * -start
                        keep_more = False
                        required_order = Order.Descending
                    else:
                        # [a:] drops from the bottom.
                        keep_tuple = (0, ) * start
                        keep_more = True
                        required_order = Order.Ascending
                else:
                    # Both are provided.
                    if start >= 0 and stop >= 0:
                        # [a:b]
                        keep_tuple = (0, ) * start + (1, ) * (stop - start)
                        keep_more = False
                        required_order = Order.Ascending
                    elif start < 0 and stop < 0:
                        # [-a:-b]
                        keep_tuple = (0, ) * -stop + (1, ) * (stop - start)
                        keep_more = False
                        required_order = Order.Descending
                    else:
                        if child_size is None:
                            raise ValueError(
                                'If both start and stop are provided, they must be both negative or both non-negative, or the size must be an inferrable constant.'
                            )
                        else:
                            ascending_keep = [0] * child_size
                            if start >= 0:
                                for i in range(start, child_size + stop):
                                    ascending_keep[i] = 1
                            else:
                                for i in range(child_size + start, stop):
                                    ascending_keep[i] = 1
                            required_order = order
                            if order > 0:
                                keep_tuple = tuple(ascending_keep)
                                keep_more = False
                            else:
                                keep_tuple = tuple(reversed(ascending_keep))
                                keep_more = False

        elif isinstance(self._index, Sequence):
            if self._index[0] == ...:
                # Type verified below.
                keep_tuple = tuple(reversed(self._index[1:]))  # type: ignore
                keep_more = False
                required_order = Order.Descending
            elif self._index[-1] == ...:
                # Type verified below.
                keep_tuple = tuple(self._index[:-1])  # type: ignore
                keep_more = False
                required_order = Order.Ascending
            else:
                raise ValueError(
                    'If a sequence is provided, either the first or last element (but not both) must be an Ellipsis (...)'
                )
            if ... in keep_tuple:
                raise ValueError(
                    'If a sequence is provided, either the first or last element (but not both) must be an Ellipsis (...)'
                )
        else:
            raise TypeError(f'Invalid type {type(self._index)} for index.')

        if required_order == order:
            state = (keep_tuple, keep_more)
            if child_size is None:
                return state, None
            more = max(child_size - len(keep_tuple), 0)
            size = sum(keep_tuple[:child_size]) + keep_more * more
            return state, size
        else:
            if child_size is None:
                raise UnsupportedOrder(
                    'Could not find supported order for keep operator without inferrable constant size.'
                )
            more = max(child_size - len(keep_tuple), 0)
            reversed_start = max(len(keep_tuple) - child_size, 0)
            reversed_tuple = (keep_more, ) * more + tuple(
                reversed(keep_tuple[reversed_start:]))
            return (reversed_tuple, False), sum(reversed_tuple)

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    arg_counts):
        keep_tuple, keep_more = state
        child_count = max(child_counts[0], 0)
        count = sum(keep_tuple[:child_count])
        if keep_more:
            count += max(child_count - len(keep_tuple), 0)
        keep_tuple = keep_tuple[child_count:]
        return (keep_tuple, keep_more), count

    @property
    def _expression_key(self):
        return MultisetKeep, self._index

    @property
    def _dungeonlet_key(self):
        return MultisetKeep

    def __str__(self) -> str:
        child = self._children[0]
        return f'{child}[{self._index}]'
