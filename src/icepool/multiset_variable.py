__docformat__ = 'google'

from icepool.order import Order, OrderReason
from icepool.multiset_expression import MultisetExpression, InitialMultisetGeneration, PopMultisetGeneration

import enum

from typing import Any, Hashable, Sequence


class MultisetBindingError(TypeError):
    """Indicates a bound multiset variable was found where a free variable was expected, or vice versa."""


class MultisetVariable(MultisetExpression[Any]):
    """A variable to be filled in with a concrete sub-expression."""

    _children = ()

    def __init__(self, is_free: bool, index: int):
        self._is_free = is_free
        self._index = index

    def outcomes(self) -> Sequence:
        raise MultisetBindingError()

    def output_arity(self) -> int:
        return 1

    def _is_resolvable(self) -> bool:
        raise MultisetBindingError()

    def _generate_initial(self) -> InitialMultisetGeneration:
        raise MultisetBindingError()

    def _generate_min(self, min_outcome) -> PopMultisetGeneration:
        raise MultisetBindingError()

    def _generate_max(self, max_outcome) -> PopMultisetGeneration:
        raise MultisetBindingError()

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    def has_free_variables(self) -> bool:
        return self._is_free

    def denominator(self) -> int:
        raise MultisetBindingError()

    def _unbind(
            self,
            bound_inputs: 'list[MultisetExpression]' = []
    ) -> 'MultisetExpression':
        if self._is_free:
            return self
        else:
            raise MultisetBindingError(
                'Attempted to unbind an expression that was already unbound.')

    @property
    def _local_hash_key(self) -> Hashable:
        return (MultisetVariable, self._is_free, self._index)

    def __str__(self) -> str:
        return f'mv[{self._index}]'
