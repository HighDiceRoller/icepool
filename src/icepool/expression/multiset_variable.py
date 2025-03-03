__docformat__ = 'google'

import icepool
from icepool.expression.base import MultisetExpressionBase
from icepool.order import Order, OrderReason
from icepool.expression.multiset_expression import MultisetExpression

import enum

from typing import Any, Hashable, Sequence


class MultisetVariable(MultisetExpression):
    """A variable to be filled in with a concrete sub-expression."""

    _children = ()

    def __init__(self,
                 is_parameter: bool,
                 index: int,
                 name: str | None = None):
        self._is_parameter = is_parameter
        self._index = index
        if name is None:
            if is_parameter:
                self._name = f'mvf[{index}]'
            else:
                self._name = f'mvb[{index}]'
        else:
            self._name = name

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
                'Attempted to detatch an expression that was already detatched.'
            )

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
