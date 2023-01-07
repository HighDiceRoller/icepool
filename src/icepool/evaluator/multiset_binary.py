"""Evaluators that merge counts from two generators according to a multiset operation."""

__docformat__ = 'google'

from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator

from abc import abstractmethod
import math

from icepool.typing import Outcome

from typing import TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""


class MultisetBinaryEvaluator(OutcomeCountEvaluator[T_contra, U_co, int]):
    """Base class for binary evaluators."""

    def __init__(self, inner: OutcomeCountEvaluator[T_contra, U_co,
                                                    int]) -> None:
        """Constructor.
        
        Args:
            inner: The evaluator to use after the counts are merged.
        """
        self._inner = inner

    @staticmethod
    @abstractmethod
    def merge_counts(left: int, right: int) -> int:
        """Merges counts from two multisets."""
        ...

    def next_state(self, state, outcome, left, right):
        """Merge the counts, then forwards to inner.
        
        Negative counts will be treated as 0.
        """
        count = self.merge_counts(left, right)
        count = max(count, 0)
        return self._inner.next_state(state, outcome, count)

    def final_outcome(self, final_state, *generators):
        """Forwards to inner."""
        return self._inner.final_outcome(final_state, *generators)

    def order(self, *generators):
        """Forwards to inner."""
        return self._inner.order(*generators)

    def alignment(self, *generators):
        """Forwards to inner."""
        return self._inner.alignment(*generators)


class MultisetUnionEvaluator(MultisetBinaryEvaluator[T_contra, U_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        if left == math.inf or right == math.inf:
            raise ValueError(
                'Multiset union cannot be taken with infinite multiplicity.')
        return max(left, right)


class MultisetIntersectionEvaluator(MultisetBinaryEvaluator[T_contra, U_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        return min(left, right)


class MultisetDifferenceEvaluator(MultisetBinaryEvaluator[T_contra, U_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        if left == math.inf:
            raise ValueError(
                'Multiset union cannot be taken with infinite multiplicity on the left.'
            )
        return left - right


class MultisetSymmetricDifferenceEvaluator(MultisetBinaryEvaluator[T_contra,
                                                                   U_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        if left == math.inf or right == math.inf:
            raise ValueError(
                'Multiset symmetric difference cannot be taken with infinite multiplicity.'
            )
        return abs(left - right)


class MultisetSumEvaluator(MultisetBinaryEvaluator[T_contra, U_co]):

    @staticmethod
    def merge_counts(left: int, right: int) -> int:
        if left == math.inf or right == math.inf:
            raise ValueError(
                'Multiset sum cannot be taken with infinite multiplicity.')
        return left + right
