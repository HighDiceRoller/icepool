__docformat__ = 'google'

import icepool
from icepool.generator.outcome_count_generator import NextOutcomeCountGenerator, OutcomeCountGenerator

from collections import defaultdict
from functools import cached_property
from typing import Any, Callable, Sequence


class SuitGenerator(OutcomeCountGenerator):
    """EXPERIMENTAL: A meta-generator that groups 2-tuple outcomes from a source generator.

    This wraps a generator whose outcomes are of the form `(face, suit)`,
    and yields `outcomes` equal to `face` and `counts` that are mappings
    from `suit` to the count of that face and suit.
    """

    def __init__(self, src: OutcomeCountGenerator, /):
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

    def _generate_min(self, min_outcome) -> NextOutcomeCountGenerator:
        blank_counts: Sequence[defaultdict[Any, int]] = [
            defaultdict(int) for _ in range(self.counts_len())
        ]
        for popped_src, counts, weights in SuitGenerator._generate_min_internal(
                min_outcome, self._src, blank_counts, 1):
            yield SuitGenerator(popped_src), counts, weights

    def _generate_max(self, max_outcome) -> NextOutcomeCountGenerator:
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
    def _key_tuple(self) -> tuple:
        return SuitGenerator, self._src

    def __eq__(self, other) -> bool:
        if not isinstance(other, SuitGenerator):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash

    @staticmethod
    def _generate_min_internal(min_outcome, src: OutcomeCountGenerator,
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
    def _generate_max_internal(max_outcome, src: OutcomeCountGenerator,
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
