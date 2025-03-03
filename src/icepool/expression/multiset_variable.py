__docformat__ = 'google'

import icepool
from icepool.expression.base import MultisetExpressionBase, MultisetVariableBase
from icepool.order import Order, OrderReason
from icepool.expression.multiset_expression import MultisetExpression

import enum

from typing import Any, Hashable, Sequence


class MultisetVariable(MultisetExpression, MultisetVariableBase):
    """A variable to be filled in with a concrete sub-expression."""

    _children = ()

    def outcomes(self) -> Sequence:
        raise icepool.MultisetVariableError()

    def _is_resolvable(self) -> bool:
        raise icepool.MultisetVariableError()

    def _generate_initial(self):
        raise icepool.MultisetVariableError()

    def _generate_min(self, min_outcome):
        raise icepool.MultisetVariableError()

    def _generate_max(self, max_outcome):
        raise icepool.MultisetVariableError()

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    def has_parameters(self) -> bool:
        return self._is_parameter

    def _detach(self, body_inputs: 'list[MultisetExpressionBase]' = []):
        if self._is_parameter:
            return self
        else:
            raise icepool.MultisetVariableError(
                'Attempted to detach an expression that was already detached.')

    def _apply_variables(self, outcome, body_counts: tuple[int, ...],
                         param_counts: tuple[int, ...]):
        if self._is_parameter:
            return self, param_counts[self._index]
        else:
            return self, body_counts[self._index]

    @property
    def _local_hash_key(self) -> Hashable:
        # name is ignored.
        return (MultisetVariable, self._is_parameter, self._index)

    def __str__(self) -> str:
        return self._name
