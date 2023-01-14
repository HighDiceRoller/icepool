"""Joint evaluators that combine the results of multiple sub-evaluators."""

__docformat__ = 'google'

import icepool
from icepool.collections import union_sorted_sets
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import Outcome, Order

from typing import Iterable, TypeVar

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
        return Order.merge(*(inner.order() for inner in self._inners))

    def alignment(self, outcomes):
        return union_sorted_sets(
            *(evaluator.alignment(outcomes) for evaluator in self._inners))

    def __str__(self) -> str:
        return 'JointEvaluator(\n' + ''.join(
            f'    {evaluator},\n' for evaluator in self._inners) + ')'


class MapEvaluator(MultisetEvaluator[T_contra, int, tuple[U_co, ...]]):
    """A `MultisetEvaluator` that jointly evaluates a single evaluator on each input multiset."""

    def __init__(self, inner: MultisetEvaluator[T_contra, int, U_co],
                 *lengths) -> None:
        """Constructor.

        Args:
            inner: The evaluator to run.
            lengths: One argument for each input of the `inner` evaluator.
                At least one must be equal to the number of groups to map over;
                the rest can be this value or 1, in which case they will be
                broadcast to all groups. For example:

                `lengths = 2, 1`: A binary evaluator will be run over each of
                the first two multisets, matched with the last each time.
                `lengths = 1, 2`: A binary evaluator will be run with the first
                multiset matched with each of the other two.
                `lengths = 2, 2`: A binary evaluator will be run with the first
                and third multiset, then the second and last.
        """
        output_len = None
        for length in lengths:
            if length > 1:
                if output_len is None:
                    output_len = length
                elif length != output_len:
                    raise ValueError(
                        f'Cannot broadcast between arities {lengths}.')
        if output_len is None:
            output_len = 1
        self._inner = inner
        self._shape = lengths
        self._output_len = output_len

    def broadcast_counts(self, *counts: int) -> Iterable[tuple[int, ...]]:
        """Broadcasts the counts, yielding each group."""
        for output_index in range(self._output_len):
            i = 0
            result: tuple[int, ...] = ()
            for length in self._shape:
                if length > 1:
                    result += (counts[i + output_index],)
                else:
                    result += (counts[i],)
                i += length
            yield result

    def next_state(self, states, outcome, *counts):
        """Runs `next_state` on each set of counts.

        The state is a tuple of the substates.
        """
        if states is None:
            return tuple(
                self._inner.next_state(None, outcome, *count_group)
                for count_group in self.broadcast_counts(*counts))
        else:
            return tuple(
                self._inner.next_state(state, outcome, *count_group)
                for state, count_group in zip(states,
                                              self.broadcast_counts(*counts)))

    def final_outcome(self, final_states):
        """Runs `final_outcome` on all final states.

        The final outcome is a tuple of the results.
        """
        if final_states is None:
            final_states = (None,) * self._output_len
        return tuple(
            self._inner.final_outcome(final_state)
            for final_state in final_states)

    def order(self):
        """Forwards to inner."""
        return self._inner.order()

    def alignment(self, outcomes):
        return self._inner.alignment(outcomes)
