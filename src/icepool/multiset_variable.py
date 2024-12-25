__docformat__ = 'google'

from icepool.generator.pop_order import PopOrderReason
from icepool.multiset_expression import MultisetExpression

from typing import Any, Hashable, Iterator, Self, Sequence

from icepool.typing import Order


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

    def _generate_initial(self) -> Iterator[tuple['MultisetExpression', int]]:
        raise UnboundMultisetExpressionError()

    def _generate_min(
            self, min_outcome
    ) -> Iterator[tuple['MultisetExpression', Sequence, int]]:
        raise UnboundMultisetExpressionError()

    def _generate_max(
            self, max_outcome
    ) -> Iterator[tuple['MultisetExpression', Sequence, int]]:
        raise UnboundMultisetExpressionError()

    def _preferred_pop_order(self) -> tuple[Order | None, PopOrderReason]:
        raise UnboundMultisetExpressionError()

    def order(self) -> Order:
        return Order.Any

    def _free_arity(self) -> int:
        return self._index + 1

    def denominator(self) -> int:
        raise UnboundMultisetExpressionError()

    def _unbind(self, next_index: int) -> 'tuple[MultisetExpression, int]':
        return self, next_index

    def _local_hash_key(self) -> Hashable:
        raise UnboundMultisetExpressionError()

    def __str__(self) -> str:
        return f'mv[{self._index}]'
