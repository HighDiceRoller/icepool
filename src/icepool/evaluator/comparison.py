"""Evaluator for comparing to a target multiset."""

__docformat__ = 'google'


from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator

from abc import abstractmethod
from collections import defaultdict

import math
from icepool.typing import Outcome, Order, ComparatorStr
from typing import Collection, Mapping, Set, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

class ComparisonEvaluator(OutcomeCountEvaluator[T_contra, bool, bool]):
    """Compares a generator to a target multiset."""

    _target: Mapping[T_contra, int | float]
    """The target multiset."""

    def __init__(self, target: Mapping[T_contra, int] | Collection[T_contra]):
        if isinstance(target, Mapping):
            self._target = {k: v for k, v in target.items()}
        elif isinstance(target, Set):
            self._target = {k: math.inf for k in target}
        else:
            self._target = defaultdict(int)
            for outcome in target:
                self._target[outcome] += 1

    @abstractmethod
    def any_all(self, outcome: T_contra, count: int) -> tuple[bool, bool]:
        """Produces a pair of bools for each outcome-count pair.
        
        The final outcome is true iff any of the first and all of the second 
        bool are `True`.
        """

    @staticmethod
    @abstractmethod
    def default_outcome() -> bool:
        """The final outcome if both self and target have no outcomes."""

    def temp(self, op: ComparatorStr,
                 target: Mapping[T_contra, int] | Collection[T_contra]):
        """Constructor.
        
        Args:
            op: The comparator to apply. Valid options are 
                <, <=, issubset, >, >=, issuperset, !=, ==, isdisjoint.
            target: The multiset to compare against. Possible types:
                * A `Mapping` from outcomes to `int`s, representing a multiset
                    with counts as the values.
                * A `Set` of outcomes. All outcomes in the target effectively
                    have unlimited multiplicity.
                * Any other `Collection`, which will be treated as a multiset.
        """
        if isinstance(target, Mapping):
            self._target = {k: v for k, v in target.items()}
        elif isinstance(target, Set):
            self._target = {k: math.inf for k in target}
        else:
            self._target = defaultdict(int)
            for outcome in target:
                self._target[outcome] += 1

        match op:
            case '<':
                def any_all(outcome: T_contra, count: int) -> tuple[bool, bool]:
                    target_count = self._target.get(outcome, 0)
                    return count < target_count, count <= target_count

                self._default_outcome = False
            case '<=' | 'issubset':
                def any_all(outcome: T_contra, count: int) -> tuple[bool, bool]:
                    target_count = self._target.get(outcome, 0)
                    return True, count <= target_count

                self._default_outcome = True
            case '>':
                def any_all(outcome: T_contra, count: int) -> tuple[bool, bool]:
                    target_count = self._target.get(outcome, 0)
                    return count > target_count, count >= target_count

                self._default_outcome = False
            case '>=' | 'issuperset':
                def any_all(outcome: T_contra, count: int) -> tuple[bool, bool]:
                    target_count = self._target.get(outcome, 0)
                    return True, count >= target_count

                self._default_outcome = True
            case '!=':
                def any_all(outcome: T_contra, count: int) -> tuple[bool, bool]:
                    target_count = self._target.get(outcome, 0)
                    return count != target_count, True

                self._default_outcome = False
            case '==':
                def any_all(outcome: T_contra, count: int) -> tuple[bool, bool]:
                    target_count = self._target.get(outcome, 0)
                    return True, count == target_count

                self._default_outcome = True
            case 'isdisjoint':
                def any_all(outcome: T_contra, count: int) -> tuple[bool, bool]:
                    target_count = self._target.get(outcome, 0)
                    both_positive = (target_count > 0) == (count > 0)
                    return True, not both_positive

                self._default_outcome = True
            case _:
                raise ValueError(f'Invalid comparator {op}.')

        self._any_all = any_all

    def next_state(self, state, outcome, count):
        """Implementation."""
        has_any, has_all = state or (False, True)
        this_any, this_all = self.any_all(outcome, count)
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
        return self._target.keys()

class IsProperSubsetEvaluator(ComparisonEvaluator[T_contra]):
    def any_all(self, outcome: T_contra, count: int) -> tuple[bool, bool]:
        target_count = self._target.get(outcome, 0)
        return count < target_count, count <= target_count
    
    @staticmethod
    def default_outcome() -> bool:
        return False

class IsSubsetEvaluator(ComparisonEvaluator[T_contra]):
    def any_all(self, outcome: T_contra, count: int) -> tuple[bool, bool]:
        target_count = self._target.get(outcome, 0)
        return True, count <= target_count
    
    @staticmethod
    def default_outcome() -> bool:
        return True

class IsProperSupersetEvaluator(ComparisonEvaluator[T_contra]):
    def any_all(self, outcome: T_contra, count: int) -> tuple[bool, bool]:
        target_count = self._target.get(outcome, 0)
        return count > target_count, count >= target_count
    
    @staticmethod
    def default_outcome() -> bool:
        return False

class IsSupersetEvaluator(ComparisonEvaluator[T_contra]):
    def any_all(self, outcome: T_contra, count: int) -> tuple[bool, bool]:
        target_count = self._target.get(outcome, 0)
        return True, count >= target_count
    
    @staticmethod
    def default_outcome() -> bool:
        return True

class IsEqualSetEvaluator(ComparisonEvaluator[T_contra]):
    def any_all(self, outcome: T_contra, count: int) -> tuple[bool, bool]:
        target_count = self._target.get(outcome, 0)
        return True, count == target_count
    
    @staticmethod
    def default_outcome() -> bool:
        return True

class IsNotEqualSetEvaluator(ComparisonEvaluator[T_contra]):
    def any_all(self, outcome: T_contra, count: int) -> tuple[bool, bool]:
        target_count = self._target.get(outcome, 0)
        return count != target_count, True
    
    @staticmethod
    def default_outcome() -> bool:
        return False

class IsDisjointSetEvaluator(ComparisonEvaluator[T_contra]):
    def any_all(self, outcome: T_contra, count: int) -> tuple[bool, bool]:
        target_count = self._target.get(outcome, 0)
        return True, not ((count > 0) and target_count > 0)
    
    @staticmethod
    def default_outcome() -> bool:
        return True
