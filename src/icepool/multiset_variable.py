__docformat__ = 'google'

from icepool.order import Order, OrderReason
from icepool.multiset_expression import MultisetExpression, InitialMultisetGeneration, PopMultisetGeneration

from typing import Any, Hashable, Sequence


class UnboundMultisetExpressionError(TypeError):
    """Indicates that an operation requiring a fully-bound multiset expression was requested on an expression with free variables."""


class MultisetVariable(MultisetExpression[Any]):
    """A free variable within the body of a @multiset_function."""
    _children = ()

    def __init__(self, index):
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

    def _free_arity(self) -> int:
        return self._index + 1

    def denominator(self) -> int:
        raise UnboundMultisetExpressionError()

    def _unbind(self, next_index: int) -> 'tuple[MultisetExpression, int]':
        return self, next_index

    @property
    def _local_hash_key(self) -> Hashable:
        return (MultisetVariable, self._index)

    def __str__(self) -> str:
        return f'mv[{self._index}]'
