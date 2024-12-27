__docformat__ = 'google'

from icepool.order import Order, OrderReason
from icepool.multiset_expression import MultisetExpression, InitialMultisetGeneration, PopMultisetGeneration

import enum

from typing import Any, Hashable, Sequence


class UnboundMultisetExpressionError(TypeError):
    """Indicates that an operation requiring a fully-bound multiset expression was requested on an expression with free variables."""


class MultisetVariable(MultisetExpression[Any]):
    """A variable to be filled in with a concrete sub-expression."""

    _children = ()

    def __init__(self, is_free: bool, index: int):
        self._is_free = is_free
        self._index = index

    def outcomes(self) -> Sequence:
        raise UnboundMultisetExpressionError()

    def output_arity(self) -> int:
        return 1

    def _is_resolvable(self) -> bool:
        raise UnboundMultisetExpressionError()

    def _generate_initial(self) -> InitialMultisetGeneration:
        raise UnboundMultisetExpressionError()

    def _generate_min(self, min_outcome) -> PopMultisetGeneration:
        raise UnboundMultisetExpressionError()

    def _generate_max(self, max_outcome) -> PopMultisetGeneration:
        raise UnboundMultisetExpressionError()

    def local_order_preference(self) -> tuple[Order | None, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    def has_free_variables(self) -> bool:
        return self._is_free

    def denominator(self) -> int:
        raise UnboundMultisetExpressionError()

    def _unbind(self, next_index: int) -> 'tuple[MultisetExpression, int]':
        return self, next_index

    @property
    def _local_hash_key(self) -> Hashable:
        return (MultisetVariable, self._index)

    def __str__(self) -> str:
        return f'mv[{self._index}]'
