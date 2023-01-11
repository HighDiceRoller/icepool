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
    """Wraps MultisetGenerator(s) so that an expression is applied to the multisets before sending the single resulting multiset forwards.

    This only supports a single output multiset, since it is only intended to
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


class MapExpressionGenerator(MultisetGenerator[T_co, tuple[int, ...]]):
    """Wraps a MultisetGenerator so that an expression is performed on each of its multisets before sending the results forward."""

    def __init__(self, generator: MultisetGenerator[T_co, tuple[int, ...]],
                 expression: 'icepool.expression.MultisetExpression') -> None:
        """Constructor.

        Args:
            generator: The generator to wrap.
            expression: The expression to evaluate on each multiset.
                This should take in a single multiset.
        """
        self._generator = generator
        self._expression = expression

    def outcomes(self) -> Sequence:
        return self._generator.outcomes()

    def counts_len(self) -> int:
        return self._generator.counts_len()

    def _is_resolvable(self) -> bool:
        return self._generator._is_resolvable()

    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
        for gen, counts, weight in self._generator._generate_min(min_outcome):
            next_counts = tuple(
                self._expression.evaluate_counts(min_outcome, count)
                for count in counts)
            next_generator = MapExpressionGenerator(gen, self._expression)
            yield next_generator, next_counts, weight

    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
        for gen, counts, weight in self._generator._generate_max(max_outcome):
            next_counts = tuple(
                self._expression.evaluate_counts(max_outcome, count)
                for count in counts)
            next_generator = MapExpressionGenerator(gen, self._expression)
            yield next_generator, next_counts, weight

    def _estimate_order_costs(self) -> tuple[int, int]:
        return self._generator._estimate_order_costs()

    def denominator(self) -> int:
        return self._generator.denominator()

    @cached_property
    def _key_tuple(self) -> tuple[Hashable, ...]:
        return MapExpressionGenerator, self._generator, self._expression
