__docformat__ = 'google'

import icepool
from icepool.generator.multiset_generator import NextMultisetGenerator, MultisetGenerator

from collections import defaultdict
from functools import cached_property
from typing import Any, Callable, Hashable, Sequence


class SuitGenerator(MultisetGenerator):
    """EXPERIMENTAL: A meta-generator that groups 2-tuple outcomes from a source generator.

    This wraps a generator whose outcomes are of the form `(face, suit)`,
    and yields `outcomes` equal to `face` and `counts` that are mappings
    from `suit` to the count of that face and suit.
    """

    def __init__(self, src: MultisetGenerator, /):
        self._src = src

    @cached_property
    def _outcomes(self) -> Sequence:
        return tuple(outcome[0] for outcome in self._src.outcomes())

    def outcomes(self) -> Sequence:
        return self._outcomes

    def counts_len(self) -> int:
        return self._src.counts_len()

    def _is_resolvable(self) -> bool:
        return self._src._is_resolvable()

    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
        blank_counts: Sequence[defaultdict[Any, int]] = [
            defaultdict(int) for _ in range(self.counts_len())
        ]
        for popped_src, counts, weights in SuitGenerator._generate_min_internal(
                min_outcome, self._src, blank_counts, 1):
            yield SuitGenerator(popped_src), counts, weights

    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
        blank_counts: Sequence[defaultdict[Any, int]] = [
            defaultdict(int) for _ in range(self.counts_len())
        ]
        for popped_src, counts, weights in SuitGenerator._generate_max_internal(
                max_outcome, self._src, blank_counts, 1):
            yield SuitGenerator(popped_src), counts, weights

    def _estimate_order_costs(self) -> tuple[int, int]:
        # We might consider up-costing this.
        return self._src._estimate_order_costs()

    def denominator(self) -> int:
        return self._src.denominator()

    @cached_property
    def _key_tuple(self) -> tuple[Hashable, ...]:
        return SuitGenerator, self._src

    @staticmethod
    def _generate_min_internal(min_outcome, src: MultisetGenerator,
                               counts: Sequence[defaultdict[Any,
                                                            int]], weight: int):
        if not src.outcomes() or src.min_outcome()[0] != min_outcome:
            yield src, counts, weight
        else:
            for sub_src, sub_counts, sub_weight in src._generate_min(
                    src.min_outcome()):
                next_counts = []
                for count, sub_count in zip(counts, sub_counts):
                    next_count = count.copy()
                    next_count[src.min_outcome()[1]] = sub_count
                    next_counts.append(next_count)
                yield from SuitGenerator._generate_min_internal(
                    min_outcome, sub_src, next_counts, weight * sub_weight)

    @staticmethod
    def _generate_max_internal(max_outcome, src: MultisetGenerator,
                               counts: Sequence[defaultdict[Any,
                                                            int]], weight: int):
        if not src.outcomes() or src.max_outcome()[0] != max_outcome:
            yield src, counts, weight
        else:
            for sub_src, sub_counts, sub_weight in src._generate_max(
                    src.max_outcome()):
                next_counts = []
                for count, sub_count in zip(counts, sub_counts):
                    next_count = count.copy()
                    next_count[src.max_outcome()[1]] = sub_count
                    next_counts.append(next_count)
                yield from SuitGenerator._generate_max_internal(
                    max_outcome, sub_src, next_counts, weight * sub_weight)
