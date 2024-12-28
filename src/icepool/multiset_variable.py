__docformat__ = 'google'

import icepool
from icepool.order import Order, OrderReason
from icepool.multiset_expression import MultisetExpression, InitialMultisetGeneration, PopMultisetGeneration

import enum

from typing import Any, Hashable, Sequence


class MultisetVariable(MultisetExpression[Any]):
    """A variable to be filled in with a concrete sub-expression."""

    _children = ()

    def __init__(self, is_free: bool, index: int, name: str | None = None):
        self._is_free = is_free
        self._index = index
        if name is None:
            if is_free:
                self._name = f'mvf[{index}]'
            else:
                self._name = f'mvb[{index}]'
        else:
            self._name = name

    def outcomes(self) -> Sequence:
        raise icepool.MultisetBindingError()

    def output_arity(self) -> int:
        return 1

    def _is_resolvable(self) -> bool:
        raise icepool.MultisetBindingError()

    def _generate_initial(self) -> InitialMultisetGeneration:
        raise icepool.MultisetBindingError()

    def _generate_min(self, min_outcome) -> PopMultisetGeneration:
        raise icepool.MultisetBindingError()

    def _generate_max(self, max_outcome) -> PopMultisetGeneration:
        raise icepool.MultisetBindingError()

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    def has_free_variables(self) -> bool:
        return self._is_free

    def denominator(self) -> int:
        raise icepool.MultisetBindingError()

    def _unbind(
            self,
            bound_inputs: 'list[MultisetExpression]' = []
    ) -> 'MultisetExpression':
        if self._is_free:
            return self
        else:
            raise icepool.MultisetBindingError(
                'Attempted to unbind an expression that was already unbound.')

    def _apply_variables(
            self, outcome, bound_counts: tuple[int, ...],
            free_counts: tuple[int, ...]) -> 'tuple[MultisetExpression, int]':
        if self._is_free:
            return self, free_counts[self._index]
        else:
            return self, bound_counts[self._index]

    @property
    def _local_hash_key(self) -> Hashable:
        # name is ignored.
        return (MultisetVariable, self._is_free, self._index)

    def __str__(self) -> str:
        return self._name
