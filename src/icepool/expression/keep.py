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
    _order: Order
    _keep_tuple: tuple[int, ...]

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
                    # No endpoints, so just return inner as-is.
                    return inner
                else:
                    if stop < 0:
                        raise ValueError(
                            'If only stop is provided, it must be non-negative.'
                        )
                    self._order = Order.Ascending
                    self._keep_tuple = (1,) * stop
            else:
                # start is not None.
                if stop is None:
                    if start >= 0:
                        raise ValueError(
                            'If only start is provided, it must be negative.')
                    self._order = Order.Descending
                    self._keep_tuple = (1,) * -start
                else:
                    # Both are provided.
                    if start >= 0 and stop >= 0:
                        self._order = Order.Ascending
                        self._keep_tuple = (0,) * start + (1,) * stop
                    elif start < 0 and stop < 0:
                        self._order = Order.Descending
                        self._keep_tuple = (0,) * -stop + (1,) * -start
                    else:
                        raise ValueError(
                            'If both start and stop are provided, they must be both negative or both not negative.'
                        )
        elif isinstance(index, Sequence):
            if index[0] == ...:
                self._order = Order.Descending
                # Type verified below.
                self._keep_tuple = tuple(index[1:])  # type: ignore
            elif index[-1] == ...:
                self._order = Order.Ascending
                # Type verified below.
                self._keep_tuple = tuple(index[:-1])  # type: ignore
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

    def next_state(self, state, outcome: T_contra, bound_counts: tuple[int,
                                                                       ...],
                   counts: tuple[int, ...]) -> tuple[Hashable, int]:
        remaining, inner_state = state or (self._keep_tuple, None)
        inner_state, count = self._inner.next_state(inner_state, outcome,
                                                    bound_counts, counts)
        if count < 0:
            raise RuntimeError(
                'KeepExpression is not compatible with incoming negative counts.'
            )

        if count > 0:
            if self._order == Order.Ascending:
                count = sum(remaining[:count])
                remaining = remaining[count:]
            else:
                count = sum(remaining[-count:])
                remaining = remaining[:-count]

        return (remaining, inner_state), count

    def order(self) -> Order:
        return Order.merge(self._order, self._inner.order())

    @cached_property
    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._inner.bound_generators()

    def bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._bound_generators

    def arity(self) -> int:
        return self._inner.arity()
