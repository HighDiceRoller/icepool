"""Basic evaluators. These all take a single generator with `int` count."""

__docformat__ = 'google'

from icepool.constant import Order
from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator
from icepool.typing import Outcome

from typing import Any, TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""


class ExpandEvaluator(OutcomeCountEvaluator[Any, tuple, int]):
    """Expands all results of a generator.

    This is expensive and not recommended unless there are few possibilities.

    Outcomes with negative count will be treated as 0 count.
    """

    def next_state(self, state, outcome, count):
        return (state or ()) + (outcome,) * count

    def order(self, *_):
        return Order.Any

    def final_outcome(self, final_state, *_):
        if final_state is None:
            return ()
        return tuple(sorted(final_state))


class SumEvaluator(OutcomeCountEvaluator[T_contra, Any, int]):
    """Sums all outcomes."""

    def next_state(self, state, outcome, count):
        """Add the outcomes to the running total. """
        if state is None:
            return outcome * count
        else:
            return state + outcome * count

    def order(self, *_):
        return Order.Any


class CountEvaluator(OutcomeCountEvaluator[T_contra, int, int]):
    """Returns the total count of outcomes.

    Usually not very interesting unless the counts are adjusted by
    `AdjustIntCountEvaluator` or other operation.
    """

    def next_state(self, state, outcome, count):
        return (state or 0) + count

    def order(self, *_):
        return Order.Any
