__docformat__ = 'google'

import icepool

from icepool.collection.counts import sorted_union
from icepool.generator.multiset_generator import InitialMultisetGenerator, NextMultisetGenerator, MultisetGenerator
from icepool.typing import Outcome, Qs, T, U

import math

from collections import defaultdict
from functools import cached_property
from types import EllipsisType
from typing import TYPE_CHECKING, Callable, Hashable, Literal, Mapping, MutableMapping, Sequence, overload

if TYPE_CHECKING:
    from icepool.expression import MultisetExpression


class MixtureGenerator(MultisetGenerator[T, tuple[int]]):
    """EXPERIMENTAL: Represents a mixture of single-output generators."""

    # Note that the total weight of an inner is the product of the factor here
    # and the denominator of the inner.
    _inners: Mapping[MultisetGenerator[T, tuple[int]], int]

    def __init__(self,
                 inners: Sequence[MultisetGenerator[T, tuple[int]]]
                 | Mapping[MultisetGenerator[T, tuple[int]], int],
                 *,
                 denominator: int | None = None):
        data: Mapping[MultisetGenerator[T, tuple[int]], int]

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

        self._inners = defaultdict(int)
        min_denominator = 0
        for inner, weight in data.items():
            factor = denominator_lcm * weight // inner.denominator(
            ) if inner.denominator() else 0
            self._inners[inner] += factor
            min_denominator += factor * inner.denominator()

        if denominator is not None:
            scale, mod = divmod(denominator, min_denominator)
            if mod != 0:
                raise ValueError(
                    f'Specified denominator of {denominator} is not consistent with the minimum possible denominator {min_denominator}.'
                )
            for inner in self._inners:
                self._inners[inner] *= scale

    def outcomes(self) -> Sequence[T]:
        return sorted_union(*(inner.outcomes() for inner in self._inners))

    def output_arity(self) -> int:
        result = None
        for inner in self._inners:
            if result is None:
                result = inner.output_arity()
            elif result != inner.output_arity():
                raise ValueError('Inconsistent output_arity.')
        if result is None:
            raise ValueError('Empty MixtureMultisetGenerator.')
        return result

    def _is_resolvable(self) -> bool:
        return all(inner._is_resolvable() for inner in self._inners)

    def _generate_initial(self) -> InitialMultisetGenerator:
        yield from self._inners.items()

    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
        raise RuntimeError(
            'MixtureMultisetGenerator should have decayed to another generator type by this point.'
        )

    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
        raise RuntimeError(
            'MixtureMultisetGenerator should have decayed to another generator type by this point.'
        )

    def _estimate_order_costs(self) -> tuple[int, int]:
        total_pop_min_cost = 0
        total_pop_max_cost = 0
        for inner in self._inners:
            pop_min_cost, pop_max_cost = inner._estimate_order_costs()
            total_pop_min_cost += pop_min_cost
            total_pop_max_cost += pop_max_cost
        return total_pop_min_cost, total_pop_max_cost

    @cached_property
    def _denominator(self) -> int:
        result = 0
        for inner, weight in self._inners.items():
            result += weight * inner.denominator()
        return result

    def denominator(self) -> int:
        return self._denominator

    @property
    def _hash_key(self) -> Hashable:
        # This is not intended to be cached directly, so we are a little loose here.
        return MixtureGenerator, tuple(self._inners.items())

    # Forwarding if inners are all KeepGenerators.

    @cached_property
    def _all_keep_generators(self) -> bool:
        return all(
            isinstance(inner, icepool.KeepGenerator) for inner in self._inners)

    def _unary_operation(self, op: Callable) -> 'MixtureGenerator[T]':
        data: MutableMapping = defaultdict(int)
        for inner, factor in self._inners.items():
            data[op(inner)] += inner.denominator() * factor
        return MixtureGenerator(data, denominator=self.denominator())

    @overload
    def keep(
            self, index: slice | Sequence[int | EllipsisType]
    ) -> 'MixtureGenerator[T]':
        ...

    @overload
    def keep(self, index: int) -> 'icepool.Die[T]':
        ...

    def keep(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'MultisetExpression[T] | icepool.Die[T] | icepool.MultisetEvaluator[T, T]':
        if self._all_keep_generators:
            result = self._unary_operation(lambda inner: inner.keep(index))
            if isinstance(index, int):
                return icepool.evaluator.KeepEvaluator().evaluate(result)
            else:
                return result
        else:
            return super().keep(index)

    def multiply_counts(self, constant: int, /) -> 'MultisetExpression[T]':
        if self._all_keep_generators:
            return self._unary_operation(
                lambda inner: inner.multiply_counts(constant))
        else:
            return super().multiply_counts(constant)

    def __str__(self) -> str:
        return 'MixtureGenerator({\n' + ',\n'.join(
            f'{k}: {v}' for k, v in self._inners.items()) + '})'
