__docformat__ = 'google'

import icepool

from icepool.evaluator.multiset_function import MultisetFunctionRawResult
from icepool.expression.multiset_expression import MultisetExpression

from collections import defaultdict

from icepool.typing import T
from types import EllipsisType
from typing import Callable, Mapping, MutableMapping, Sequence, overload


class MultisetMixture(MultisetExpression[T]):
    """Represents a mixture of multiset expressions."""

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

    def _prepare(self):
        for inner, weight in self._inner_expressions.items():
            for dungeonlets, questlets, sources, inner_weight in inner._prepare(
            ):
                yield dungeonlets, questlets, sources, inner_weight * weight

    @property
    def _has_parameter(self):
        return any(inner._has_parameter for inner in self._inner_expressions)

    # Forwarding if inners are all KeepGenerators.

    @property
    def _static_keepable(self) -> bool:
        return all(inner._static_keepable for inner in self._inner_expressions)

    def _unary_operation(self, op: Callable) -> 'MultisetMixture[T]':
        data: MutableMapping = defaultdict(int)
        for inner, factor in self._inner_expressions.items():
            data[op(inner)] += factor
        return MultisetMixture(data)

    @overload
    def keep(
            self, index: slice | Sequence[int | EllipsisType]
    ) -> 'MultisetMixture[T]':
        ...

    @overload
    def keep(self, index: int) -> 'icepool.Die[T]':
        ...

    def keep(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'MultisetExpression[T] | icepool.Die[T] | icepool.MultisetEvaluator[T, T] | MultisetFunctionRawResult[T, T]':
        if self._static_keepable:
            result = self._unary_operation(lambda inner: inner.keep(index))
            if isinstance(index, int):
                return icepool.evaluator.keep_evaluator.evaluate(result,
                                                                 index=None)
            else:
                return result
        else:
            return super().keep(index)

    def multiply_counts(self, constant: int, /) -> 'MultisetExpression[T]':
        if self._static_keepable:
            return self._unary_operation(
                lambda inner: inner.multiply_counts(constant))
        else:
            return super().multiply_counts(constant)

    @property
    def hash_key(self):
        return MultisetMixture, tuple(self._inner_expressions.items())

    def __str__(self) -> str:
        return 'MultisetMixture({\n' + ',\n'.join(
            f'{k}: {v}' for k, v in self._inner_expressions.items()) + '})'
