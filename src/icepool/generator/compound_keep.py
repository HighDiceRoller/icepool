__docformat__ = 'google'

import icepool
from icepool.generator.keep import KeepGenerator, pop_max_from_keep_tuple, pop_min_from_keep_tuple
from icepool.generator.multiset_generator import MultisetGenerator
from icepool.order import Order, OrderReason, merge_order_preferences

import itertools
import math

from typing import Hashable, Iterator, Sequence
from icepool.typing import T


class CompoundKeepGenerator(KeepGenerator[T]):
    _inner_generators: tuple[KeepGenerator[T], ...]

    def __init__(self, inners: Sequence[KeepGenerator[T]],
                 keep_tuple: Sequence[int]):
        self._inner_generators = tuple(inners)
        self._keep_tuple = tuple(keep_tuple)

    def outcomes(self) -> Sequence[T]:
        return icepool.sorted_union(*(inner.outcomes()
                                      for inner in self._inner_generators))

    def _is_resolvable(self) -> bool:
        return all(inner._is_resolvable() for inner in self._inner_generators)

    def _prepare(self):
        yield self, 1

    def _generate_min(
            self,
            min_outcome) -> Iterator[tuple['CompoundKeepGenerator', int, int]]:
        for t in itertools.product(*(inner._generate_min(min_outcome)
                                     for inner in self._inner_generators)):
            generators, counts, weights = zip(*t)
            total_count = sum(counts)
            total_weight = math.prod(weights)
            popped_keep_tuple, result_count = pop_min_from_keep_tuple(
                self._keep_tuple, total_count)
            yield CompoundKeepGenerator(
                generators, popped_keep_tuple), result_count, total_weight

    def _generate_max(
            self,
            max_outcome) -> Iterator[tuple['CompoundKeepGenerator', int, int]]:
        for t in itertools.product(*(inner._generate_max(max_outcome)
                                     for inner in self._inner_generators)):
            generators, counts, weights = zip(*t)
            total_count = sum(counts)
            total_weight = math.prod(weights)
            popped_keep_tuple, result_count = pop_max_from_keep_tuple(
                self._keep_tuple, total_count)
            yield CompoundKeepGenerator(
                generators, popped_keep_tuple), result_count, total_weight

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return merge_order_preferences(*(inner.local_order_preference()
                                         for inner in self._inner_generators))

    def _set_keep_tuple(self, keep_tuple: tuple[int,
                                                ...]) -> 'KeepGenerator[T]':
        return CompoundKeepGenerator(self._inner_generators, keep_tuple)

    @property
    def _local_hash_key(self) -> Hashable:
        return CompoundKeepGenerator, tuple(
            inner._hash_key
            for inner in self._inner_generators), self._keep_tuple

    def __str__(self) -> str:
        return ('CompoundKeep([' +
                ', '.join(str(inner) for inner in self._inner_generators) +
                '], keep_tuple=' + str(self.keep_tuple()) + ')')
