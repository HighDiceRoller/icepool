"""Joint evaluators that combine the results of multiple sub-evaluators."""

__docformat__ = 'google'

from functools import cached_property
import itertools
import icepool
from icepool.order import Order
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import T

from typing import Collection, Iterable, Iterator


class JointEvaluator(MultisetEvaluator[T, tuple]):
    """A `MultisetEvaluator` that jointly evaluates sub-evaluators on the same set of input generators."""

    def __init__(self, *sub_evaluators: MultisetEvaluator) -> None:
        self._sub_evaluators = sub_evaluators

    def next_state(self, state, outcome, *counts):
        """Runs `next_state` for all sub-evaluator.

        The state is a tuple of the sub-states.

        If any sub-evaluator returns `Reroll`, the result as a whole is `Reroll`.
        """
        extra_counts = counts[:self._extra_arity]
        counts = counts[self._extra_arity:]

        if state is None:
            result = tuple(
                evaluator.next_state(
                    None,
                    outcome,
                    *subeval_extra_counts,
                    *counts,
                ) for evaluator, subeval_extra_counts in zip(
                    self._sub_evaluators,
                    self._split_extra_counts(*extra_counts)))
        else:
            result = tuple(
                evaluator.next_state(
                    substate,
                    outcome,
                    *subeval_extra_counts,
                    *counts,
                ) for evaluator, substate, subeval_extra_counts in zip(
                    self._sub_evaluators, state,
                    self._split_extra_counts(*extra_counts)))
        if icepool.Reroll in result:
            return icepool.Reroll
        else:
            return result

    def final_outcome(self, final_state) -> 'tuple | icepool.RerollType':
        """Runs `final_state` for all sub-evaluators.

        The final outcome is a tuple of the final suboutcomes.

        If any sub-evaluator returns `Reroll`, the result as a whole is `Reroll`.
        """
        if final_state is None:
            result = tuple(
                subeval.final_outcome(None)
                for subeval in self._sub_evaluators)
        else:
            result = tuple(
                subeval.final_outcome(final_substate) for subeval,
                final_substate in zip(self._sub_evaluators, final_state))
        if icepool.Reroll in result:
            return icepool.Reroll
        else:
            return result

    def order(self) -> Order:
        """Determines the common order of the sub-evaluators.

        Raises:
            ValueError: If sub-evaluators have conflicting orders, i.e. some are
                ascending and others are descending.
        """
        return Order.merge(*(subeval.order()
                             for subeval in self._sub_evaluators))

    def extra_outcomes(self, outcomes) -> Collection[T]:
        return icepool.sorted_union(*(subeval.extra_outcomes(outcomes)
                                      for subeval in self._sub_evaluators))

    @cached_property
    def _bound_inputs(self) -> 'tuple[icepool.MultisetExpression, ...]':
        return tuple(
            itertools.chain.from_iterable(subeval.bound_inputs()
                                          for subeval in self._sub_evaluators))

    def bound_inputs(self) -> 'tuple[icepool.MultisetExpression, ...]':
        return self._bound_inputs

    @cached_property
    def _extra_arity(self) -> int:
        return sum(expression.output_arity()
                   for expression in self.bound_inputs())

    @cached_property
    def _extra_slices(self) -> tuple[slice, ...]:
        """Precomputed slices for determining which extra counts go with which sub-evaluator."""
        result = []
        index = 0
        for subeval in self._sub_evaluators:
            counts_length = sum(expression.output_arity()
                                for expression in subeval.bound_inputs())
            result.append(slice(index, index + counts_length))
            index += counts_length
        return tuple(result)

    def _split_extra_counts(self, *extra_counts:
                            int) -> Iterator[tuple[int, ...]]:
        for index in self._extra_slices:
            yield extra_counts[index]

    def __str__(self) -> str:
        return 'JointEvaluator(\n' + ''.join(
            f'    {subeval},\n' for subeval in self._sub_evaluators) + ')'
