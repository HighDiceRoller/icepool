"""Evaluator for comparing to a target multiset."""

__docformat__ = 'google'


from icepool.constant import Order
from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator

from collections import defaultdict

from icepool.typing import Outcome
from typing import Collection, Mapping, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

class ComparisonEvaluator(OutcomeCountEvaluator[T_contra, bool, bool]):
    """Compares a generator to a target multiset."""

    _target: Mapping[T_contra, int]
    """The target multiset."""
    _default_outcome: bool
    """Outcome to be used if both self and target are empty."""

    def __init__(self, op: str,
                 target: Mapping[T_contra, int] | Collection[T_contra]):
        if isinstance(target, Mapping):
            self._target = {k: v for k, v in target.items()}
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
        this_any, this_all = self._any_all(outcome, count)
        has_all = has_all and this_all
        has_any = has_all and (has_any or this_any)
        return has_any, has_all

    def final_outcome(self, final_state, *_):
        """Implementation."""
        if final_state is None:
            return self._default_outcome
        has_any, has_all = final_state
        return has_any and has_all

    def order(self, *_):
        """Allows any order."""
        return Order.Any

    def alignment(self, *_):
        """Implementation."""
        return self._target.keys()
