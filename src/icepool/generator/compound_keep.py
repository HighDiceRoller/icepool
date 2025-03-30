__docformat__ = 'google'

import icepool
from icepool.generator.keep import KeepGenerator, KeepSource, pop_max_from_keep_tuple, pop_min_from_keep_tuple
from icepool.generator.multiset_generator import MultisetSource
from icepool.order import Order, OrderReason, merge_order_preferences

import itertools
import math

from typing import Sequence
from icepool.typing import T


class CompoundKeepGenerator(KeepGenerator[T]):
    _inner_generators: tuple[KeepGenerator[T], ...]

    def __init__(self, inners: Sequence[KeepGenerator[T]],
                 keep_tuple: Sequence[int]):
        self._inner_generators = tuple(inners)
        self._keep_tuple = tuple(keep_tuple)

    def _make_source(self):
        inner_sources = tuple(generator._make_source()
                              for generator in self._inner_generators)
        return CompoundKeepSource(inner_sources, self._keep_tuple)

    def _set_keep_tuple(self, keep_tuple: tuple[int,
                                                ...]) -> 'KeepGenerator[T]':
        return CompoundKeepGenerator(self._inner_generators, keep_tuple)

    @property
    def hash_key(self):
        return CompoundKeepGenerator, self._inner_generators, self._keep_tuple

    def __str__(self) -> str:
        return ('CompoundKeep([' +
                ', '.join(str(inner) for inner in self._inner_generators) +
                '], keep_tuple=' + str(self.keep_tuple()) + ')')


class CompoundKeepSource(KeepSource[T]):

    def __init__(self, inner_sources: tuple[MultisetSource, ...],
                 keep_tuple: tuple[int, ...]):
        self.inner_sources = inner_sources
        self.keep_tuple = keep_tuple

    def outcomes(self):
        return icepool.sorted_union(*(inner.outcomes()
                                      for inner in self.inner_sources))

    def pop(self, order: Order, outcome: T):
        if order > 0:
            pop_from_keep_tuple = pop_min_from_keep_tuple
        else:
            pop_from_keep_tuple = pop_max_from_keep_tuple

        for t in itertools.product(*(inner.pop(order, outcome)
                                     for inner in self.inner_sources)):
            sources, counts, weights = zip(*t)
            total_count = sum(counts)
            total_weight = math.prod(weights)
            popped_keep_tuple, result_count = pop_from_keep_tuple(
                self.keep_tuple, total_count)
            yield CompoundKeepSource(
                sources, popped_keep_tuple), result_count, total_weight

    def order_preference(self) -> tuple[Order, OrderReason]:
        return merge_order_preferences(*(inner.order_preference()
                                         for inner in self.inner_sources))

    def is_resolvable(self) -> bool:
        return all(inner.is_resolvable() for inner in self.inner_sources)

    @property
    def hash_key(self):
        return CompoundKeepSource, self.inner_sources, self.keep_tuple
