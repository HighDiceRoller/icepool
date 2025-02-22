__docformat__ = 'google'

import icepool

from icepool.multiset_expression import MultisetArityError, MultisetExpression, InitialMultisetGeneration, PopMultisetGeneration
from icepool.generator.multiset_generator import MultisetGenerator
from icepool.order import Order, OrderReason, merge_order_preferences

import math

from collections import defaultdict
from functools import cached_property

from icepool.typing import Qs, T, U
from types import EllipsisType
from typing import TYPE_CHECKING, Callable, Hashable, Literal, Mapping, MutableMapping, Sequence, overload


class MultisetMixture(MultisetExpression[T]):
    """EXPERIMENTAL: Represents a mixture of multiset expressions."""

    _children = ()

    # Note that the total weight of an inner is the product of the factor here
    # and the denominator of the inner.
    _inner_expressions: Mapping[MultisetExpression[T], int]

    def __init__(self,
                 inners: Sequence[MultisetExpression[T]]
                 | Mapping[MultisetExpression[T], int],
                 *,
                 denominator: int | None = None):
        data: Mapping[MultisetExpression[T], int]

        if isinstance(inners, Mapping):
            data = {inner: weight for inner, weight in inners.items()}
        else:
            data = defaultdict(int)
            for inner in inners:
                data[inner] += 1

        denominator_lcm = math.lcm(
            *(inner.denominator() // math.gcd(inner.denominator(), weight)
              for inner, weight in data.items()
              if inner.denominator() > 0 and weight > 0))

        self._inner_expressions = defaultdict(int)
        min_denominator = 0
        for inner, weight in data.items():
            factor = denominator_lcm * weight // inner.denominator(
            ) if inner.denominator() else 0
            self._inner_expressions[inner] += factor
            min_denominator += factor * inner.denominator()

        if denominator is not None:
            scale, mod = divmod(denominator, min_denominator)
            if mod != 0:
                raise ValueError(
                    f'Specified denominator of {denominator} is not consistent with the minimum possible denominator {min_denominator}.'
                )
            for inner in self._inner_expressions:
                self._inner_expressions[inner] *= scale

    def outcomes(self) -> Sequence[T]:
        return icepool.sorted_union(*(inner.outcomes()
                                      for inner in self._inner_expressions))

    def output_arity(self) -> int:
        result = None
        for inner in self._inner_expressions:
            if result is None:
                result = inner.output_arity()
            elif result != inner.output_arity():
                raise MultisetArityError('Inconsistent output_arity.')
        if result is None:
            raise ValueError('Empty MultisetMixture.')
        return result

    def _is_resolvable(self) -> bool:
        return all(inner._is_resolvable() for inner in self._inner_expressions)

    def _generate_initial(self) -> InitialMultisetGeneration:
        yield from self._inner_expressions.items()

    def _generate_min(self, min_outcome) -> PopMultisetGeneration:
        raise RuntimeError(
            'MultisetMixture should have decayed to another generator type by this point.'
        )

    def _generate_max(self, max_outcome) -> PopMultisetGeneration:
        raise RuntimeError(
            'MultisetMixture should have decayed to another generator type by this point.'
        )

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return merge_order_preferences(*(inner.local_order_preference()
                                         for inner in self._inner_expressions))

    def has_free_variables(self):
        return any(inner.has_free_variables()
                   for inner in self._inner_expressions)

    @cached_property
    def _denominator(self) -> int:
        result = 0
        for inner, weight in self._inner_expressions.items():
            result += weight * inner.denominator()
        return result

    def denominator(self) -> int:
        return self._denominator

    def _unbind(
            self,
            bound_inputs: 'list[MultisetExpression]' = []
    ) -> 'MultisetExpression':
        raise RuntimeError(
            'MultisetMixture should have decayed to another generator type by this point.'
        )

    def _apply_variables(
            self, outcome: T, bound_counts: tuple[int, ...],
            free_counts: tuple[int,
                               ...]) -> 'tuple[MultisetExpression[T], int]':
        raise RuntimeError(
            'MultisetMixture should have decayed to another generator type by this point.'
        )

    @property
    def _local_hash_key(self) -> Hashable:
        # This is not intended to be cached directly, so we are a little loose here.
        return MultisetMixture, tuple(self._inner_expressions.items())

    # Forwarding if inners are all KeepGenerators.

    @property
    def _can_keep(self) -> bool:
        return all(inner._can_keep for inner in self._inner_expressions)

    def _unary_operation(self, op: Callable) -> 'MultisetMixture[T]':
        data: MutableMapping = defaultdict(int)
        for inner, factor in self._inner_expressions.items():
            data[op(inner)] += inner.denominator() * factor
        return MultisetMixture(data, denominator=self.denominator())

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
    ) -> 'MultisetExpression[T] | icepool.Die[T] | icepool.MultisetEvaluator[T, T]':
        if self._can_keep:
            result = self._unary_operation(lambda inner: inner.keep(index))
            if isinstance(index, int):
                return icepool.evaluator.KeepEvaluator().evaluate(result)
            else:
                return result
        else:
            return super().keep(index)

    def multiply_counts(self, constant: int, /) -> 'MultisetExpression[T]':
        if self._can_keep:
            return self._unary_operation(
                lambda inner: inner.multiply_counts(constant))
        else:
            return super().multiply_counts(constant)

    def __str__(self) -> str:
        return 'MultisetMixture({\n' + ',\n'.join(
            f'{k}: {v}' for k, v in self._inner_expressions.items()) + '})'
