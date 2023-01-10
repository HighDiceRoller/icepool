__docformat__ = 'google'

import icepool.expression

from icepool.generator.multiset_generator import NextMultisetGenerator, MultisetGenerator
from icepool.typing import Outcome

import itertools
import math
from functools import cached_property

from typing import Callable, Collection, Hashable, Mapping, Sequence, TypeAlias, TypeVar

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""Type variable representing the outcome type."""

Qints_co = TypeVar('Qints_co', bound=tuple[int, ...], covariant=True)
"""Type variable representing the counts type, which is a tuple of `int`s."""


class ExpressionGenerator(MultisetGenerator[T_co, tuple[int]]):
    """Wraps MultisetGenerator(s) so that an evaluation is performed on them before sending to an evaluator.

    This only supports a single output count, since it is only intended to
    implement shortcuts for evaluating generators.
    """

    def __init__(self, *generators: MultisetGenerator[T_co, tuple[int, ...]],
                 expression: 'icepool.expression.MultisetExpression') -> None:
        self._generators = generators
        self._expression = expression

    @cached_property
    def _outcomes(self) -> Sequence:
        all_outcomes = set.union(
            *(set(generator.outcomes()) for generator in self._generators))
        return tuple(sorted(all_outcomes))

    def outcomes(self) -> Sequence:
        return self._outcomes

    def counts_len(self) -> int:
        return 1

    def _is_resolvable(self) -> bool:
        return all(generator._is_resolvable() for generator in self._generators)

    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
        for t in itertools.product(*(generator._generate_min(min_outcome)
                                     for generator in self._generators)):
            generators, counts, weights = zip(*t)

            next_generator = ExpressionGenerator(*generators,
                                                 expression=self._expression)
            merged_counts = itertools.chain.from_iterable(counts)
            next_count = self._expression.evaluate_counts(
                min_outcome, *merged_counts)
            next_weights = math.prod(weights)
            yield next_generator, (next_count,), next_weights

    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
        for t in itertools.product(*(generator._generate_max(max_outcome)
                                     for generator in self._generators)):
            generators, counts, weights = zip(*t)

            next_generator = ExpressionGenerator(*generators,
                                                 expression=self._expression)
            merged_counts = itertools.chain.from_iterable(counts)
            next_count = self._expression.evaluate_counts(
                max_outcome, *merged_counts)
            next_weights = math.prod(weights)
            yield next_generator, (next_count,), next_weights

    def _estimate_order_costs(self) -> tuple[int, int]:
        left = 1
        right = 1
        for generator in self._generators:
            l, r = generator._estimate_order_costs()
            left *= l
            right *= r
        return left, right

    def denominator(self) -> int:
        return math.prod(
            generator.denominator() for generator in self._generators)

    @cached_property
    def _key_tuple(self) -> tuple[Hashable, ...]:
        return ExpressionGenerator, self._generators, self._expression
