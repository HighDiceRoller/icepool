"""Joint evaluators that combine the results of multiple sub-evaluators."""

__docformat__ = 'google'

import icepool
from icepool.collections import union_sorted_sets
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import Outcome, Order

from typing import TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""

Q_contra = TypeVar('Q_contra', contravariant=True)
"""Type variable representing the count type. This may be replaced with a `TypeVarTuple` in the future."""


class JointEvaluator(MultisetEvaluator[T_contra, Q_contra, tuple]):
    """A `MultisetEvaluator` that jointly evaluates sub-evaluators on the same set of input generators."""

    def __init__(self, *inners: MultisetEvaluator):
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

    def final_outcome(self, final_state):
        """Runs `final_state` for all subevals.

        The final outcome is a tuple of the final suboutcomes.
        """
        return tuple(
            inner.final_outcome(final_substate)
            for inner, final_substate in zip(self._inners, final_state))

    def order(self):
        """Determines the common order of the subevals.

        Raises:
            ValueError: If subevals have conflicting orders, i.e. some are
                ascending and others are descending.
        """
        suborders = tuple(inner.order() for inner in self._inners)
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

    def alignment(self, outcomes):
        return union_sorted_sets(
            *(evaluator.alignment(outcomes) for evaluator in self._inners))

    def __str__(self) -> str:
        return 'JointEvaluator(\n' + ''.join(
            f'    {evaluator},\n' for evaluator in self._inners) + ')'


class MapEvaluator(MultisetEvaluator[T_contra, int, tuple[U_co, ...]]):
    """A `MultisetEvaluator` that jointly evaluates a single evaluator on each input multiset."""

    def __init__(self, inner: MultisetEvaluator[T_contra, int, U_co]) -> None:
        self._inner = inner

    def next_state(self, states, outcome, *counts):
        """Runs `next_state` on each count.

        The state is a tuple of the substates.
        """
        if states is None:
            return tuple(
                self._inner.next_state(None, outcome, count)
                for count in counts)
        else:
            return tuple(
                self._inner.next_state(state, outcome, count)
                for state, count in zip(states, counts))

    def final_outcome(self, final_states):
        """Runs `final_outcome` on all final states.

        The final outcome is a tuple of the results.
        """
        return tuple(
            self._inner.final_outcome(final_state)
            for final_state in final_states)

    def order(self):
        """Forwards to inner."""
        return self._inner.order()

    def alignment(self, outcomes):
        return self._inner.alignment(outcomes)
