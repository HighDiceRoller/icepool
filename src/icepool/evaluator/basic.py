"""Basic evaluators."""

__docformat__ = 'google'

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import Outcome, Order

from typing import Any, Callable, Final, Hashable, Mapping, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""

Q_contra = TypeVar('Q_contra', contravariant=True)
"""Type variable representing the count type. This may be replaced with a `TypeVarTuple` in the future."""


class WrapFuncEvaluator(MultisetEvaluator[T_contra, Q_contra, U_co]):
    """Evaluates the provided function."""

    def __init__(self, func: Callable[..., U_co], /):
        """Constructs a new instance given the function that should be called for `next_state()`.
        Args:
            func(state, outcome, *counts): This should take the same arguments
                as `next_state()`, minus `self`, and return the next state.
        """
        self._func = func

    def next_state(self, state: Hashable, outcome: T_contra, *counts: Q_contra):
        """Calls the wrapped function."""
        return self._func(state, outcome, *counts)


class ExpandEvaluator(MultisetEvaluator[Outcome, int, tuple]):
    """Expands all results of a generator.

    This is expensive and not recommended unless there are few possibilities.

    Outcomes with negative count will be treated as 0 count.
    """

    def next_state(self, state, outcome, count):
        """Implementation."""
        return (state or ()) + (outcome,) * count

    def order(self):
        """Allows any order."""
        return Order.Any

    def final_outcome(self, final_state):
        """Implementation."""
        if final_state is None:
            return ()
        return tuple(sorted(final_state))


class SumEvaluator(MultisetEvaluator[Outcome, int, Any]):
    """Sums all outcomes."""

    def __init__(self, map: Callable | Mapping | None = None) -> None:
        """Constructor.

        map: If provided, outcomes will be mapped according to this just
            before summing.
        """
        if map is None:

            def map_func(outcome):
                return outcome

            self._map = map_func
        elif callable(map):
            self._map = map
        else:
            map_dict = {k: v for k, v in map.items()}

            def map_func(outcome):
                return map_dict[outcome]

            self._map = map_func

    def next_state(self, state, outcome, count):
        """Implementation."""
        outcome = self._map(outcome)
        if state is None:
            return outcome * count
        else:
            return state + outcome * count

    def order(self):
        """Allows any order."""
        return Order.Any


sum_evaluator: Final = SumEvaluator()
"""Shared instance for caching."""


class CountEvaluator(MultisetEvaluator[Outcome, int, int]):
    """Returns the total count of outcomes.

    Usually not very interesting unless the counts are adjusted by
    `AdjustIntCountEvaluator`.
    """

    def next_state(self, state, outcome, count):
        """Implementation."""
        return (state or 0) + count

    def final_outcome(self, final_state):
        """Implementation."""
        return final_state or 0

    def order(self):
        """Allows any order."""
        return Order.Any


count_evaluator: Final = CountEvaluator()
"""Shared instance for caching."""
