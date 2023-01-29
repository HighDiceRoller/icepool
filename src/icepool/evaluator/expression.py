__docformat__ = 'google'

from functools import cached_property
import itertools
import icepool
import icepool.expression

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import Order, Outcome, T_contra, U_co

from typing import Collection, Iterable


class ExpressionEvaluator(MultisetEvaluator[T_contra, U_co]):
    """Assigns an expression to be evaluated first to each input of an evaluator."""

    def __init__(
            self,
            *expressions: 'icepool.expression.MultisetExpression[T_contra]',
            evaluator: MultisetEvaluator[T_contra, U_co],
            truth_value: bool | None = None) -> None:
        self._evaluator = evaluator
        self._expressions = expressions
        self._truth_value = truth_value

    def next_state(self, state, outcome, *counts):
        """Adjusts the counts, then forwards to inner."""
        if state is None:
            expression_states = (None,) * len(self._expressions)
            evaluator_state = None
        else:
            expression_states, evaluator_state = state

        bound_counts = counts[:self._bound_arity]
        prefix_counts = counts[self._bound_arity:self._bound_arity +
                               len(self._evaluator.prefix_generators())]
        counts = counts[self._bound_arity +
                        len(self._evaluator.prefix_generators()):]

        expression_states, expression_counts = zip(*(expression._next_state(
            expression_state,
            outcome,
            expression_bound_counts,
            counts,
        ) for expression, expression_state, expression_bound_counts in zip(
            self._expressions, expression_states,
            self._split_bound_counts(*bound_counts))))
        evaluator_state = self._evaluator.next_state(evaluator_state, outcome,
                                                     *prefix_counts,
                                                     *expression_counts)
        return expression_states, evaluator_state

    def final_outcome(
            self,
            final_state) -> 'U_co | icepool.Die[U_co] | icepool.RerollType':
        if final_state is None:
            return self._evaluator.final_outcome(None)
        else:
            _, evaluator_state = final_state
        return self._evaluator.final_outcome(evaluator_state)

    def order(self) -> Order:
        """Forwards to inner."""
        expression_order = Order.merge(
            *(expression._order() for expression in self._expressions))
        return Order.merge(expression_order, self._evaluator.order())

    def alignment(self, *generators) -> Collection[T_contra]:
        """Forwards to inner."""
        return self._evaluator.alignment(*generators)

    @cached_property
    def _prefix_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._bound_generators + self._evaluator.prefix_generators()

    def prefix_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._prefix_generators

    def validate_arity(self, arity: int) -> None:
        if arity < self._cached_arity:
            raise ValueError(
                f'Expected arity of {self._cached_arity}, got {arity}.')

    @cached_property
    def _cached_arity(self) -> int:
        """The number of input multisets."""
        return max((expression._arity() for expression in self._expressions),
                   default=0)

    def arity(self) -> int:
        return self._cached_arity

    @cached_property
    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        """The entire flattened list of bound generators."""
        return tuple(
            itertools.chain.from_iterable(expression._bound_generators()
                                          for expression in self._expressions))

    @cached_property
    def _bound_arity(self) -> int:
        return len(self._bound_generators)

    def _split_bound_counts(self,
                            *bound_counts: int) -> 'Iterable[tuple[int, ...]]':
        """Splits a tuple of counts into one set of bound counts per expression."""
        index = 0
        for expression in self._expressions:
            counts_length = len(expression._bound_generators())
            yield bound_counts[index:index + counts_length]
            index += counts_length

    def __bool__(self) -> bool:
        if self._truth_value is None:
            raise TypeError(
                'MultisetExpression only has a truth value if it is the result of the == or != operator.'
            )
        return self._truth_value

    def __str__(self) -> str:
        if len(self._expressions) == 1:
            return f'{self._expressions[0]} -> {self._evaluator}'
        else:
            return '(' + ', '.join(
                str(expression)
                for expression in self._expressions) + ') -> ' + str(
                    type(self._evaluator))
