"""Evaluator for comparing two multisets of outcomes."""

__docformat__ = 'google'

from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator

from abc import abstractmethod
from collections import defaultdict

import math
from icepool.typing import Outcome, Order, SetComparatorStr
from typing import Collection, Mapping, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""


class ComparisonEvaluator(OutcomeCountEvaluator[T_contra, int, bool]):
    """Compares the multisets produced by two generators, or a left generator and a fixed right side."""

    _right: Mapping[T_contra, int | float] | None
    """The right-hand multiset, if fixed."""

    def __init__(self,
                 right: Mapping[T_contra, int] |
                 Collection[T_contra] | None = None):
        """Constructor.

        Args:
            right: If not provided, the evaulator will take left and right
                generators as arguments to `evaluate()`.
                If provided, this will be used as the right-hand side of the
                comparison, and `evaluate()` will only take a left generator.
        """
        if right is None:
            self._right = None
        elif isinstance(right, Mapping):
            self._right = {k: v for k, v in right.items()}
        else:
            self._right = defaultdict(int)
            for outcome in right:
                self._right[outcome] += 1


    @classmethod
    def new_by_name(cls, name: SetComparatorStr, right: Mapping[T_contra, int] |
                 Collection[T_contra] | None = None) -> 'ComparisonEvaluator[T_contra]':
        """Creates a new instance by the operation name."""
        match name:
            case '<': return IsProperSubsetEvaluator(right)
            case '<=' | 'issubset': return IsSubsetEvaluator(right)
            case '>': return IsProperSubsetEvaluator(right)
            case '>=' | 'issuperset': return IsSupersetEvaluator(right)
            case '==': return IsEqualSetEvaluator(right)
            case '!=': return IsNotEqualSetEvaluator(right)
            case 'isdisjoint': return IsDisjointSetEvaluator(right)
            case _: raise ValueError(f'Invalid comparator {name}.')


    @abstractmethod
    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        """Called for each outcome and produces a pair of bools.

        The final outcome is true iff any of the first and all of the second
        bool are `True`.
        """

    @staticmethod
    @abstractmethod
    def default_outcome() -> bool:
        """The final outcome if both left and right have no outcomes."""

    def next_state(self, state, outcome, left, right=None):
        """Implementation."""
        if self._right is not None:
            right = self._right.get(outcome, 0)
        has_any, has_all = state or (False, True)
        this_any, this_all = self.any_all(left, right)
        has_all = has_all and this_all
        has_any = has_all and (has_any or this_any)
        return has_any, has_all

    def final_outcome(self, final_state, *_):
        """Implementation."""
        if final_state is None:
            return self.default_outcome()
        has_any, has_all = final_state
        return has_any and has_all

    def order(self, *_):
        """Allows any order."""
        return Order.Any

    def alignment(self, *_):
        """Implementation."""
        if self._right is not None:
            return self._right.keys()
        else:
            return ()


class IsProperSubsetEvaluator(ComparisonEvaluator[T_contra]):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return left < right, left <= right

    @staticmethod
    def default_outcome() -> bool:
        return False


class IsSubsetEvaluator(ComparisonEvaluator[T_contra]):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return True, left <= right

    @staticmethod
    def default_outcome() -> bool:
        return True


class IsProperSupersetEvaluator(ComparisonEvaluator[T_contra]):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return left > right, left >= right

    @staticmethod
    def default_outcome() -> bool:
        return False


class IsSupersetEvaluator(ComparisonEvaluator[T_contra]):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return True, left >= right

    @staticmethod
    def default_outcome() -> bool:
        return True


class IsEqualSetEvaluator(ComparisonEvaluator[T_contra]):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return True, left == right

    @staticmethod
    def default_outcome() -> bool:
        return True


class IsNotEqualSetEvaluator(ComparisonEvaluator[T_contra]):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return left != right, True

    @staticmethod
    def default_outcome() -> bool:
        return False


class IsDisjointSetEvaluator(ComparisonEvaluator[T_contra]):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return True, not ((left > 0) and right > 0)

    @staticmethod
    def default_outcome() -> bool:
        return True
