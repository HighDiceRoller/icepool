"""Joint evaluators that combine the results of multiple sub-evaluators."""

__docformat__ = 'google'

import icepool
from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator
from icepool.typing import Outcome, Order

from typing import TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""

Q_contra = TypeVar('Q_contra', contravariant=True)
"""Type variable representing the count type. This may be replaced with a `TypeVarTuple` in the future."""


class JointEvaluator(OutcomeCountEvaluator[T_contra, Q_contra, tuple]):
    """An `OutcomeCountEvaluator` that jointly evaluates sub-evaluators on the same roll(s) of a generator."""

    def __init__(self, *inners: OutcomeCountEvaluator):
        self._inners = inners

    def next_state(self, state, outcome, *counts):
        """Runs `next_state` for all subevals.

        The state is a tuple of the substates.
        """
        if state is None:
            return tuple(
                evaluator.next_state(None, outcome, *counts)
                for evaluator in self._inners)
        else:
            return tuple(
                evaluator.next_state(substate, outcome, *counts)
                for evaluator, substate in zip(self._inners, state))

    def final_outcome(self, final_state,
                      *generators: icepool.OutcomeCountGenerator):
        """Runs `final_state` for all subevals.

        The final outcome is a tuple of the final suboutcomes.
        """
        if final_state is None:
            final_state = (None,) * len(generators)
        return tuple(
            inner.final_outcome(final_substate, *generators)
            for inner, final_substate in zip(self._inners, final_state))

    def order(self, *generators: icepool.OutcomeCountGenerator):
        """Determines the common order of the subevals.

        Raises:
            ValueError: If subevals have conflicting orders, i.e. some are
                ascending and others are descending.
        """
        suborders = tuple(inner.order(*generators) for inner in self._inners)
        ascending = any(x > 0 for x in suborders)
        descending = any(x < 0 for x in suborders)
        if ascending and descending:
            raise ValueError('Sub-evals have conflicting orders.')
        elif ascending:
            return Order.Ascending
        elif descending:
            return Order.Descending
        else:
            return Order.Any