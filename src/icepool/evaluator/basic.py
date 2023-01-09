"""Basic evaluators."""

__docformat__ = 'google'

from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator
from icepool.typing import Outcome, Order

from typing import Any, Callable, Final, Hashable, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""

Q_contra = TypeVar('Q_contra', contravariant=True)
"""Type variable representing the count type. This may be replaced with a `TypeVarTuple` in the future."""


class WrapFuncEvaluator(OutcomeCountEvaluator[T_contra, Q_contra, U_co]):
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


class ExpandEvaluator(OutcomeCountEvaluator[Outcome, int, tuple]):
    """Expands all results of a generator.

    This is expensive and not recommended unless there are few possibilities.

    Outcomes with negative count will be treated as 0 count.
    """

    def next_state(self, state, outcome, count):
        """Implementation."""
        return (state or ()) + (outcome,) * count

    def order(self, *_):
        """Allows any order."""
        return Order.Any

    def final_outcome(self, final_state, *_):
        """Implementation."""
        if final_state is None:
            return ()
        return tuple(sorted(final_state))


class SumEvaluator(OutcomeCountEvaluator[Outcome, int, Any]):
    """Sums all outcomes."""

    def next_state(self, state, outcome, count):
        """Implementation."""
        if state is None:
            return outcome * count
        else:
            return state + outcome * count

    def order(self, *_):
        """Allows any order."""
        return Order.Any


sum_evaluator: Final = SumEvaluator()
"""Shared instance for caching."""


class CountEvaluator(OutcomeCountEvaluator[Outcome, int, int]):
    """Returns the total count of outcomes.

    Usually not very interesting unless the counts are adjusted by
    `AdjustIntCountEvaluator`.
    """

    def next_state(self, state, outcome, count):
        """Implementation."""
        return (state or 0) + count

    def final_outcome(self, final_state, *_):
        """Implementation."""
        return final_state or 0

    def order(self, *_):
        """Allows any order."""
        return Order.Any


count_evaluator: Final = CountEvaluator()
"""Shared instance for caching."""
