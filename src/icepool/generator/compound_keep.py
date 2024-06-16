__docformat__ = 'google'

import icepool
from icepool.collection.counts import sorted_union
from icepool.generator.keep import KeepGenerator, pop_max_from_keep_tuple, pop_min_from_keep_tuple
from icepool.generator.multiset_generator import InitialMultisetGenerator, NextMultisetGenerator, MultisetGenerator

import itertools
import math

from typing import Hashable, Sequence
from icepool.typing import T


class CompoundKeepGenerator(KeepGenerator[T]):
    _inners: tuple[KeepGenerator[T], ...]

    def __init__(self, inners: Sequence[KeepGenerator[T]],
                 keep_tuple: Sequence[int]):
        self._inners = tuple(inners)
        self._keep_tuple = tuple(keep_tuple)

    def outcomes(self) -> Sequence[T]:
        return sorted_union(*(inner.outcomes() for inner in self._inners))

    def output_arity(self) -> int:
        return 1

    def _is_resolvable(self) -> bool:
        return all(inner._is_resolvable() for inner in self._inners)

    def _generate_initial(self) -> InitialMultisetGenerator:
        yield self, 1

    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
        for t in itertools.product(*(inner._generate_min(min_outcome)
                                     for inner in self._inners)):
            generators, counts, weights = zip(*t)
            total_count = sum(count[0] for count in counts)
            total_weight = math.prod(weights)
            popped_keep_tuple, result_count = pop_min_from_keep_tuple(
                self._keep_tuple, total_count)
            yield CompoundKeepGenerator(
                generators, popped_keep_tuple), (result_count, ), total_weight

    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
        for t in itertools.product(*(inner._generate_max(max_outcome)
                                     for inner in self._inners)):
            generators, counts, weights = zip(*t)
            total_count = sum(count[0] for count in counts)
            total_weight = math.prod(weights)
            popped_keep_tuple, result_count = pop_max_from_keep_tuple(
                self._keep_tuple, total_count)
            yield CompoundKeepGenerator(
                generators, popped_keep_tuple), (result_count, ), total_weight

    def _estimate_order_costs(self) -> tuple[int, int]:
        total_pop_min_cost = 1
        total_pop_max_cost = 1
        for inner in self._inners:
            pop_min_cost, pop_max_cost = inner._estimate_order_costs()
            total_pop_min_cost *= pop_min_cost
            total_pop_max_cost *= pop_max_cost
        return total_pop_min_cost, total_pop_max_cost

    def denominator(self) -> int:
        return math.prod(inner.denominator() for inner in self._inners)

    def _set_keep_tuple(self, keep_tuple: tuple[int,
                                                ...]) -> 'KeepGenerator[T]':
        return CompoundKeepGenerator(self._inners, keep_tuple)

    @property
    def _hash_key(self) -> Hashable:
        return CompoundKeepGenerator, tuple(
            inner._hash_key for inner in self._inners), self._keep_tuple

    def __str__(self) -> str:
        return ('CompoundKeep([' +
                ', '.join(str(inner) for inner in self._inners) +
                '], keep_tuple=' + str(self.keep_tuple()) + ')')
