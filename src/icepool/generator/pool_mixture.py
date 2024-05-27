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

    # Note that the weight here effectively multiplies the denominator of the
    # corresponding subgenerator itself.
    _sub_pools: Mapping[Pool[T], int]

    def __init__(self, sub_pools: Sequence[Pool[T]] | Mapping[Pool[T], int], *,
                 denominator: int | None):
        data: Mapping[Pool[T], int]

        if isinstance(sub_pools, Mapping):
            data = {sub_pool: weight for sub_pool, weight in sub_pools.items()}
        else:
            data = defaultdict(int)
            for sub_pool in sub_pools:
                data[sub_pool] += 1

        denominator_lcm = math.lcm(
            *(sub_pool.denominator() //
              math.gcd(sub_pool.denominator(), weight)
              for sub_pool, weight in data.items()
              if sub_pool.denominator() > 0 and weight > 0))

        self._sub_pools = defaultdict(int)
        min_denominator = 0
        for sub_pool, weight in data.items():
            factor = denominator_lcm * weight // sub_pool.denominator(
            ) if sub_pool.denominator() else 0
            self._sub_pools[sub_pool] += factor
            min_denominator += factor * sub_pool.denominator()

        if denominator is not None:
            scale, mod = divmod(denominator, min_denominator)
            if mod != 0:
                raise ValueError(
                    f'Specified denominator of {denominator} is not consistent with the minimum possible denominator {min_denominator}.'
                )
            for sub_pool in self._sub_pools:
                self._sub_pools[sub_pool] *= scale

    def outcomes(self) -> Sequence[T]:
        return sorted_union(*(sub_pool.outcomes()
                              for sub_pool in self._sub_pools))

    def output_arity(self) -> int:
        result = None
        for sub_pool in self._sub_pools:
            if result is None:
                result = sub_pool.output_arity()
            elif result != sub_pool.output_arity():
                raise ValueError('Inconsistent output_arity.')
        if result is None:
            raise ValueError('Empty MixtureMultisetGenerator.')
        return result

    def _is_resolvable(self) -> bool:
        return all(sub_pool._is_resolvable() for sub_pool in self._sub_pools)

    def _generate_initial(self) -> InitialMultisetGenerator:
        yield from self._sub_pools.items()

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
        for sub_pool in self._sub_pools:
            pop_min_cost, pop_max_cost = sub_pool._estimate_order_costs()
            total_pop_min_cost += pop_min_cost
            total_pop_max_cost += pop_max_cost
        return total_pop_min_cost, total_pop_max_cost

    @cached_property
    def _denominator(self) -> int:
        result = 0
        for sub_pool, weight in self._sub_pools.items():
            result += weight * sub_pool.denominator()
        return result

    def denominator(self) -> int:
        return self._denominator

    @property
    def _hash_key(self) -> Hashable:
        # This is not intended to be cached directly, so we are a little loose here.
        return PoolMixture, tuple(self._sub_pools.items())

    # Mapping pool specializations.
    def unary_operator(self, op: Callable[..., Pool[U]]) -> 'PoolMixture[U]':
        data: MutableMapping = defaultdict(int)
        for k, v in self._sub_pools.items():
            data[op(k)] += v
        return PoolMixture(data)

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
        for k, v in self._sub_pools.items():
            data[k.keep(index)] += v
        if isinstance(index, int):
            return icepool.Die(data)
        else:
            return PoolMixture(data)

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
