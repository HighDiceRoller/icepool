__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression_base import MultisetExpressionBase
from icepool.expression.multiset_expression import MultisetArityError, MultisetExpression
from icepool.generator.multiset_generator import MultisetGenerator
from icepool.order import Order, OrderReason, merge_order_preferences

import math

from collections import defaultdict
from functools import cached_property

from icepool.typing import T, U
from types import EllipsisType
from typing import TYPE_CHECKING, Callable, Hashable, Literal, Mapping, MutableMapping, Sequence, overload


class MultisetMixture(MultisetExpression[T]):
    """EXPERIMENTAL: Represents a mixture of multiset expressions."""

    _children = ()

    _inner_expressions: Mapping[MultisetExpression[T], int]

    def __init__(self, inners: Sequence[MultisetExpression[T]]
                 | Mapping[MultisetExpression[T], int]):

        if isinstance(inners, Mapping):
            self._inner_expressions = {
                inner: weight
                for inner, weight in inners.items()
            }
        else:
            self._inner_expressions = defaultdict(int)
            for inner in inners:
                self._inner_expressions[inner] += 1

    def outcomes(self) -> Sequence[T]:
        return icepool.sorted_union(*(inner.outcomes()
                                      for inner in self._inner_expressions))

    def _is_resolvable(self) -> bool:
        return all(inner._is_resolvable() for inner in self._inner_expressions)

    def _prepare(self):
        yield from self._inner_expressions.items()

    def _generate_min(self, min_outcome):
        raise RuntimeError(
            'MultisetMixture should have decayed to another generator type by this point.'
        )

    def _generate_max(self, max_outcome):
        raise RuntimeError(
            'MultisetMixture should have decayed to another generator type by this point.'
        )

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return merge_order_preferences(*(inner.local_order_preference()
                                         for inner in self._inner_expressions))

    def has_parameters(self):
        return any(inner.has_parameters() for inner in self._inner_expressions)

    def _detach(
        self,
        body_inputs: 'list[MultisetExpressionBase]' = []
    ) -> 'MultisetExpression[T]':
        raise RuntimeError(
            'MultisetMixture should have decayed to another generator type by this point.'
        )

    def _apply_variables(
            self, outcome: T, body_counts: tuple[int, ...],
            param_counts: tuple[int,
                                ...]) -> 'tuple[MultisetExpression[T], int]':
        raise RuntimeError(
            'MultisetMixture should have decayed to another generator type by this point.'
        )

    def __str__(self) -> str:
        return 'MultisetMixture({\n' + ',\n'.join(
            f'{k}: {v}' for k, v in self._inner_expressions.items()) + '})'
