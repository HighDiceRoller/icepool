__docformat__ = 'google'

import icepool

from icepool.generator.pool import Pool
from icepool.collection.counts import sorted_union
from icepool.generator.multiset_generator import InitialMultisetGenerator, NextMultisetGenerator, MultisetGenerator
from icepool.typing import Outcome, Qs, T, U

import math

from collections import defaultdict
from functools import cached_property
from types import EllipsisType
from typing import Callable, Hashable, Literal, Mapping, MutableMapping, Sequence, overload


class PoolMixture(MultisetGenerator[T, tuple[int]]):
    """EXPERIMENTAL: Represents a mixture of pools."""

    # Note that the total weight of a subpool is the product of the factor here
    # and the denominator of the subpool.
    _inners: Mapping[Pool[T], int]

    def __init__(self,
                 inners: Sequence[Pool[T]] | Mapping[Pool[T], int],
                 *,
                 denominator: int | None = None):
        data: Mapping[Pool[T], int]

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
        return PoolMixture, tuple(self._inners.items())

    # Mapping pool specializations.
    def unary_operator(self, op: Callable[..., Pool[U]]) -> 'PoolMixture[U]':
        data: MutableMapping = defaultdict(int)
        for inner, factor in self._inners.items():
            data[op(inner)] += inner.denominator() * factor
        return PoolMixture(data, denominator=self.denominator())

    @overload
    def keep(self,
             index: slice | Sequence[int | EllipsisType]) -> 'PoolMixture[T]':
        ...

    @overload
    def keep(self, index: int) -> 'icepool.Die[T]':
        ...

    def keep(
        self, index: slice | Sequence[int | EllipsisType] | int
    ) -> 'PoolMixture[T] | icepool.Die[T]':
        data: MutableMapping = defaultdict(int)
        for inner, factor in self._inners.items():
            data[inner.keep(index)] += inner.denominator() * factor
        if isinstance(index, int):
            return icepool.Die(data)
        else:
            return PoolMixture(data, denominator=self.denominator())

    @overload
    def __getitem__(
            self,
            index: slice | Sequence[int | EllipsisType]) -> 'PoolMixture[T]':
        ...

    @overload
    def __getitem__(self, index: int) -> 'icepool.Die[T]':
        ...

    def __getitem__(
        self, index: int | slice | Sequence[int | EllipsisType]
    ) -> 'PoolMixture[T] | icepool.Die[T]':
        return self.keep(index)

    def lowest(self,
               keep: int | None = None,
               drop: int | None = None) -> 'PoolMixture[T]':
        return self.unary_operator(lambda p: p.lowest(keep, drop))

    def highest(self,
                keep: int | None = None,
                drop: int | None = None) -> 'PoolMixture[T]':
        return self.unary_operator(lambda p: p.highest(keep, drop))

    def middle(self,
               keep: int = 1,
               *,
               tie: Literal['error', 'high',
                            'low'] = 'error') -> 'PoolMixture[T]':
        return self.unary_operator(lambda p: p.middle(keep, tie=tie))

    def __mul__(self, other: int) -> 'PoolMixture[T]':
        return self.unary_operator(lambda p: p.multiply_counts(other))

    # Commutable in this case.
    def __rmul__(self, other: int) -> 'PoolMixture[T]':
        return self.unary_operator(lambda p: p.multiply_counts(other))

    def multiply_counts(self, constant: int, /) -> 'PoolMixture[T]':
        return self.unary_operator(lambda p: p.multiply_counts(constant))
