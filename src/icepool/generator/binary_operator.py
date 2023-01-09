"""Binary operators between two generators."""

__docformat__ = 'google'

from icepool.generator.outcome_count_generator import NextOutcomeCountGenerator, OutcomeCountGenerator
from icepool.typing import Outcome, MultisetBinaryOperationStr

import itertools
from abc import abstractmethod
from functools import cached_property

from typing import Sequence, TypeVar

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""Type variable representing the outcome type."""

class BinaryOperatorGenerator(OutcomeCountGenerator[T_co, tuple[int]]):

    def __init__(self,
                 left: OutcomeCountGenerator[T_co, tuple[int]],
                 right: OutcomeCountGenerator[T_co, tuple[int]]) -> None:
        self._left = left
        self._right = right

    @classmethod
    def new_by_name(self,
                    name: MultisetBinaryOperationStr,
                    left: OutcomeCountGenerator[T_co, tuple[int]],
                    right: OutcomeCountGenerator[T_co, tuple[int]]) -> 'BinaryOperatorGenerator[T_co]':
        match name:
            case '+' | 'disjoint_sum': return DisjointUnionGenerator(left, right)
            case '-' | 'difference': return DifferenceGenerator(left, right)
            case '|' | 'union': return UnionGenerator(left, right)
            case '&' | 'intersection': return IntersectionGenerator(left, right)
            case '^' | 'symmetric_difference': return SymmetricDifferenceGenerator(left, right)
            case _: raise ValueError(f'Invalid operator {name}.')

    @staticmethod
    @abstractmethod
    def merge_counts(left: int, right: int) -> int:
        """Merge counts produced by the left and right generator."""

    @cached_property
    def _outcomes(self) -> Sequence[T_co]:
        all_outcomes = set(self._left.outcomes()) | set(self._right.outcomes())
        return tuple(sorted(all_outcomes))

    def outcomes(self) -> Sequence[T_co]:
        return self._outcomes

    def counts_len(self) -> int:
        """The number of counts generated. Must be constant."""
        return 1

    def _is_resolvable(self) -> bool:
        return self._left._is_resolvable() and self._right._is_resolvable()

    def _generate_min(self, min_outcome) -> NextOutcomeCountGenerator:
        for (left_generator, left_counts,
             left_weight), (right_generator, right_counts,
                            right_weight) in itertools.product(
                                self._left._generate_min(min_outcome),
                                self._right._generate_min(min_outcome)):
            next_generator = self.__class__(left_generator, right_generator)
            next_counts = self.merge_counts(left_counts[0], right_counts[0])
            next_counts = max(next_counts, 0)
            next_weight = left_weight * right_weight
            yield next_generator, (next_counts,), next_weight

    def _generate_max(self, max_outcome) -> NextOutcomeCountGenerator:
        for (left_generator, left_counts,
             left_weight), (right_generator, right_counts,
                            right_weight) in itertools.product(
                                self._left._generate_max(max_outcome),
                                self._right._generate_max(max_outcome)):
            next_generator = self.__class__(left_generator, right_generator)
            next_counts = self.merge_counts(left_counts[0], right_counts[0])
            next_counts = max(next_counts, 0)
            next_weight = left_weight * right_weight
            yield next_generator, (next_counts,), next_weight

    def _estimate_order_costs(self) -> tuple[int, int]:
        left_costs = self._left._estimate_order_costs()
        right_costs = self._right._estimate_order_costs()
        return left_costs[0] * right_costs[0], left_costs[1] * right_costs[1]

    def denominator(self) -> int:
        return self._left.denominator() * self._right.denominator()

    @cached_property
    def _key_tuple(self) -> tuple:
        return self.__class__, self._left, self._right

    def equals(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash


class IntersectionGenerator(BinaryOperatorGenerator[T_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return min(left, right)


class DifferenceGenerator(BinaryOperatorGenerator[T_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left - right


class UnionGenerator(BinaryOperatorGenerator[T_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return max(left, right)


class DisjointUnionGenerator(BinaryOperatorGenerator[T_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return left + right


class SymmetricDifferenceGenerator(BinaryOperatorGenerator[T_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return abs(max(left, 0) - max(right, 0))
