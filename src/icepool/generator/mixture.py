__docformat__ = 'google'

import icepool

from icepool.collection.counts import sorted_union
from icepool.generator.multiset_generator import InitialMultisetGenerator, NextMultisetGenerator, MultisetGenerator
from icepool.typing import Outcome, Qs, T

from collections import defaultdict
from typing import Hashable, Mapping, Sequence


class MixtureMultisetGenerator(MultisetGenerator[T, Qs]):
    """EXPERIMENTAL: Represents a mixture of multiset generators."""

    _sub_generators: Mapping[MultisetGenerator[T, Qs], int]

    def __init__(self, sub_generators: Sequence[MultisetGenerator[T, Qs]]
                 | Mapping[MultisetGenerator[T, Qs], int]):
        if isinstance(sub_generators, Mapping):
            self._sub_generators = {
                sub_generator: weight
                for sub_generator, weight in sub_generators.items()
            }
        else:
            self._sub_generators = defaultdict(int)
            for sub_generator in sub_generators:
                self._sub_generators[sub_generator] += 1

    def outcomes(self) -> Sequence[T]:
        return sorted_union(*(sub_generator.outcomes()
                              for sub_generator in self._sub_generators))

    def output_arity(self) -> int:
        result = None
        for sub_generator in self._sub_generators:
            if result is None:
                result = sub_generator.output_arity()
            elif result != sub_generator.output_arity():
                raise ValueError('Inconsistent output_arity.')
        if result is None:
            raise ValueError('Empty MixtureMultisetGenerator.')
        return result

    def _is_resolvable(self) -> bool:
        return all(sub_generator._is_resolvable()
                   for sub_generator in self._sub_generators)

    def _generate_initial(self) -> InitialMultisetGenerator:
        for sub_generator, weight in self._sub_generators.items():
            for sub_sub_generator, sub_weight in sub_generator._generate_initial(
            ):
                yield sub_sub_generator, weight * sub_weight

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
        for sub_generator in self._sub_generators:
            pop_min_cost, pop_max_cost = sub_generator._estimate_order_costs()
            total_pop_min_cost += pop_min_cost
            total_pop_max_cost += pop_max_cost
        return total_pop_min_cost, total_pop_max_cost

    def denominator(self) -> int:
        result = 0
        for sub_generator, weight in self._sub_generators.items():
            result += weight * sub_generator.denominator()
        return result

    @property
    def _hash_key(self) -> Hashable:
        # This is not intended to be cached directly, so we are a little loose here.
        return MixtureMultisetGenerator, tuple(self._sub_generators.items())
