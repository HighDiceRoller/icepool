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

    def __init__(self, *children: MultisetEvaluator) -> None:
        self._children = children

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
                    *evaluator_extra_counts,
                    *counts,
                ) for evaluator, evaluator_extra_counts in zip(
                    self._children, self._split_extra_counts(*extra_counts)))
        else:
            result = tuple(
                evaluator.next_state(
                    substate,
                    outcome,
                    *evaluator_extra_counts,
                    *counts,
                ) for evaluator, substate, evaluator_extra_counts in zip(
                    self._children, state,
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
                child.final_outcome(None) for child in self._children)
        else:
            result = tuple(
                child.final_outcome(final_substate)
                for child, final_substate in zip(self._children, final_state))
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
        return Order.merge(*(child.order() for child in self._children))

    def extra_outcomes(self, outcomes) -> Collection[T]:
        return icepool.sorted_union(*(evaluator.extra_outcomes(outcomes)
                                      for evaluator in self._children))

    @cached_property
    def _extra_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return tuple(
            itertools.chain.from_iterable(expression.extra_generators()
                                          for expression in self._children))

    def extra_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._extra_generators

    def validate_arity(self, arity: int) -> None:
        for evaluator in self._children:
            evaluator.validate_arity(arity)

    @cached_property
    def _extra_arity(self) -> int:
        return sum(generator.output_arity()
                   for generator in self.extra_generators())

    @cached_property
    def _extra_slices(self) -> tuple[slice, ...]:
        """Precomputed slices for determining which extra counts go with which sub-evaluator."""
        result = []
        index = 0
        for expression in self._children:
            counts_length = sum(generator.output_arity()
                                for generator in expression.extra_generators())
            result.append(slice(index, index + counts_length))
            index += counts_length
        return tuple(result)

    def _split_extra_counts(self, *extra_counts:
                            int) -> Iterator[tuple[int, ...]]:
        for index in self._extra_slices:
            yield extra_counts[index]

    def __str__(self) -> str:
        return 'JointEvaluator(\n' + ''.join(
            f'    {evaluator},\n' for evaluator in self._children) + ')'
