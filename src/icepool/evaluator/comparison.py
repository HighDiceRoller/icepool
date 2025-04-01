"""Evaluator for comparing two multisets of outcomes."""

__docformat__ = 'google'

from icepool.evaluator.multiset_evaluator import MultisetEvaluator

from abc import abstractmethod

from typing import Any


class ComparisonEvaluator(MultisetEvaluator[Any, bool]):
    """Compares the multisets produced by two generators."""

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

    def next_state(self, state, order, outcome, left, right):
        """Implementation."""
        has_any, has_all = state or (False, True)
        this_any, this_all = self.any_all(left, right)
        has_all = has_all and this_all
        has_any = has_all and (has_any or this_any)
        return has_any, has_all

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, left_size, right_size) -> bool:
        """Implementation."""
        if final_state is None:
            return self.default_outcome()
        has_any, has_all = final_state
        return has_any and has_all

    @property
    def next_state_key(self):
        return type(self)


class IsProperSubsetEvaluator(ComparisonEvaluator):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return left < right, left <= right

    @staticmethod
    def default_outcome() -> bool:
        return False


class IsSubsetEvaluator(ComparisonEvaluator):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return True, left <= right

    @staticmethod
    def default_outcome() -> bool:
        return True


class IsProperSupersetEvaluator(ComparisonEvaluator):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return left > right, left >= right

    @staticmethod
    def default_outcome() -> bool:
        return False


class IsSupersetEvaluator(ComparisonEvaluator):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return True, left >= right

    @staticmethod
    def default_outcome() -> bool:
        return True


class IsEqualSetEvaluator(ComparisonEvaluator):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return True, left == right

    @staticmethod
    def default_outcome() -> bool:
        return True


class IsNotEqualSetEvaluator(ComparisonEvaluator):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return left != right, True

    @staticmethod
    def default_outcome() -> bool:
        return False


class IsDisjointSetEvaluator(ComparisonEvaluator):

    def any_all(self, left: int, right: int) -> tuple[bool, bool]:
        return True, not (left > 0 and right > 0)

    @staticmethod
    def default_outcome() -> bool:
        return True
