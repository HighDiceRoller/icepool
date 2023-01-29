"""Joint evaluators that combine the results of multiple sub-evaluators."""

__docformat__ = 'google'

from functools import cached_property
import itertools
import icepool
from icepool.collections import sorted_union
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import Outcome, Order, T_contra, U_co

from typing import Collection, Iterable, Iterator


class JointEvaluator(MultisetEvaluator[T_contra, tuple]):
    """A `MultisetEvaluator` that jointly evaluates sub-evaluators on the same set of input generators."""

    def __init__(self, *inners: MultisetEvaluator) -> None:
        self._inners = inners

    def next_state(self, state, outcome, *counts):
        """Runs `next_state` for all subevals.

        The state is a tuple of the substates.
        """
        prefix_counts = counts[:self._extra_arity]
        counts = counts[self._extra_arity:]

        if state is None:
            return tuple(
                evaluator.next_state(
                    None,
                    outcome,
                    *evaluator_prefix_counts,
                    *counts,
                ) for evaluator, evaluator_prefix_counts in zip(
                    self._inners, self._split_prefix_counts(*prefix_counts)))
        else:
            return tuple(
                evaluator.next_state(
                    substate,
                    outcome,
                    *evaluator_prefix_counts,
                    *counts,
                ) for evaluator, substate, evaluator_prefix_counts in zip(
                    self._inners, state,
                    self._split_prefix_counts(*prefix_counts)))

    def final_outcome(self, final_state) -> tuple:
        """Runs `final_state` for all subevals.

        The final outcome is a tuple of the final suboutcomes.
        """
        return tuple(
            inner.final_outcome(final_substate)
            for inner, final_substate in zip(self._inners, final_state))

    def order(self) -> Order:
        """Determines the common order of the subevals.

        Raises:
            ValueError: If subevals have conflicting orders, i.e. some are
                ascending and others are descending.
        """
        return Order.merge(*(inner.order() for inner in self._inners))

    def alignment(self, outcomes) -> Collection[T_contra]:
        return sorted_union(
            *(evaluator.alignment(outcomes) for evaluator in self._inners))

    @cached_property
    def _prefix_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return tuple(
            itertools.chain.from_iterable(
                expression.prefix_generators() for expression in self._inners))

    def prefix_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._prefix_generators

    def validate_arity(self, arity: int) -> None:
        for evaluator in self._inners:
            evaluator.validate_arity(arity)

    @cached_property
    def _extra_arity(self) -> int:
        return sum(
            generator.output_arity() for generator in self.prefix_generators())

    def _split_prefix_counts(self,
                             *extra_counts: int) -> Iterator[tuple[int, ...]]:
        index = 0
        for expression in self._inners:
            counts_length = sum(generator.output_arity()
                                for generator in expression.prefix_generators())
            yield extra_counts[index:index + counts_length]
            index += counts_length

    def __str__(self) -> str:
        return 'JointEvaluator(\n' + ''.join(
            f'    {evaluator},\n' for evaluator in self._inners) + ')'
