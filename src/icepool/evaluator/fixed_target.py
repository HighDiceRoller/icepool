__docformat__ = 'google'

import icepool
from icepool.constant import Order
from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator

from collections import defaultdict
import math

from icepool.typing import Outcome
from abc import ABC, abstractmethod
from typing import Any, Callable, Collection, Generic, Hashable, Mapping, Set, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""


class FixedTargetEvaluator(OutcomeCountEvaluator[T_contra, U_co, int]):

    def __init__(self,
            target: Mapping[Outcome, int] | Set[Outcome] | Collection[Outcome] | None = None,
            *,
            invert: bool = False,
            min_count: int | None = None,
            div_count: int | None = None,
            max_count: int | None = None) -> None:
        self._min_count = min_count
        self._adjust_count = FixedTargetEvaluator._make_adjust_count(
            target, invert=invert, min_count=min_count, div_count=div_count, max_count=max_count)

    @staticmethod
    def _make_adjust_count(
            target: Mapping[Outcome, int] | Set[Outcome] | Collection[Outcome] | None = None,
            *,
            invert: bool = False,
            min_count: int | None = None,
            div_count: int | None = None,
            max_count: int | None = None) -> Callable[[Outcome, int], int]:
        """
        The args are applied in the order presented above and below.

        Args:
            target: If provided, an intersection or difference will be taken
                with this. Possible types:
                * A `Mapping` from outcomes to `int`s, representing a multiset
                    with counts as the values.
                * A `Set` of outcomes. All outcomes in the target effectively
                    have unlimited multiplicity.
                * Any other `Collection`, which will be treated as a multiset.
            invert: If `False` (default), the intersection will be taken with
                `target`. Otherwise, the difference will be taken. If `target`
                is not provided, this value is ignored.
            min_count: If provided, any outcome with less than this count will
                produce a 0 count. For example, `min_count=2` will ignore
                anything that's not a matching pair or better.
            div_count: If provided, counts will be divided by this value
                (rounding down). For example, `floordiv=2` will count the number
                of matching pairs.
            max_count: Any outcome with greater than this count will be treated
                as having this count. For example, `max_count=1` will count
                duplicates only once.

                `max_count` can be less than `min_count`. For example,
                `min_count=2, max_count=1` will count outcomes that are pairs
                or better, but only contributing a count of 1 per pair.
        """
        if target is None and min_count is None and div_count is None and max_count is None:

            def identity_count(_: Outcome, count: int) -> int:
                """Returns the count, unmodified."""
                return count

            return identity_count

        if target is None:
            invert = True
            target_dict = {}
        elif isinstance(target, Mapping):
            target_dict = {k: v for k, v in target.items()}
        elif isinstance(target, Set):
            target_dict = {k: math.inf for k in target}
        else:
            target_dict = defaultdict(int)
            for outcome in target:
                target_dict[outcome] += 1

        def adjust_count(outcome: Outcome, count: int) -> int:
            """Adjusts the count based on arguments to a constructed TargetSetEvaluator."""
            if min_count is not None and count < min_count:
                return 0
            if div_count is not None:
                count //= div_count
            if max_count is not None:
                count = min(count, max_count)
            if invert:
                # Set difference.
                return max(count - target_dict.get(outcome, 0), 0)
            else:
                # Set intersection.
                return min(count, target_dict.get(outcome, 0))

        return adjust_count

    def next_state(self, state, outcome, count):
        count = self._adjust_count(outcome, count)
        return self.next_state_with_adjusted_count(state, outcome, count)

    @abstractmethod
    def next_state_with_adjusted_count(self, state: Hashable, outcome: T_contra,
                                       count: int) -> Hashable:
        """As next_state, but after counts have been adjusted."""
        ...

    def order(self, *_):
        return Order.Any


class ExpandEvaluator(FixedTargetEvaluator[T_contra, tuple[T_contra, ...]]):

    def next_state_with_adjusted_count(self, state, outcome, count):
        return (state or ()) + (outcome,) * count

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return ()
        return tuple(sorted(final_state))


class SumEvaluator(FixedTargetEvaluator[T_contra, Any]):

    def __init__(self,
            target: Mapping[Outcome, int] | Set[Outcome] | Collection[Outcome] | None = None,
            *,
            invert: bool = False,
            min_count: int | None = None,
            div_count: int | None = None,
            max_count: int | None = None, map: Mapping[T_contra, Any] | Callable[[T_contra], Any] | None) -> None:
        FixedTargetEvaluator.__init__(self, target, invert=invert, min_count=min_count, div_count=div_count, max_count=max_count)
        if map is None:
            def map_func(outcome: T_contra):
                return outcome
        elif callable(map):
            def map_func(outcome: T_contra):
                return map(outcome)  # type: ignore
        else:
            map_dict = {k:v for k, v in map.items()}
            def map_func(outcome: T_contra):
                return map_dict.get(outcome, outcome)

        self._map = map_func


    def next_state_with_adjusted_count(self, state, outcome, count):
        outcome = self._map(outcome)
        if state is None:
            return outcome * count
        else:
            return state + outcome * count


class AllMatchingSetsEvaluator(FixedTargetEvaluator[T_contra, tuple[int, ...]]):

    def next_state_with_adjusted_count(self, state, _, count):
        if self._min_count is not None and count < self._min_count:
            return state
        state = (state or ()) + (count,)
        return tuple(sorted(state))

    def final_outcome(self, final_state, *_):
        return final_state or ()


class CountEvaluator(FixedTargetEvaluator[T_contra, int]):

    def next_state_with_adjusted_count(self, state, _, count):
        return (state or 0) + count

    def final_outcome(self, final_state, *_):
        return final_state or 0


class FixedTargetComparator(OutcomeCountEvaluator[T_contra, bool, bool]):

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
        has_any, has_all = state or (False, True)
        this_any, this_all = self._any_all(outcome, count)
        has_all = has_all and this_all
        has_any = has_all and (has_any or this_any)
        return has_any, has_all

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return self._default_outcome
        has_any, has_all = final_state
        return has_any and has_all

    def order(self, *_):
        return Order.Any

    def alignment(self, *_):
        return self._target.keys()
