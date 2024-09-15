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

    def __init__(self,
                 *expressions:
                 'icepool.expression.MultisetExpression[T_contra]',
                 evaluator: MultisetEvaluator[T_contra, U_co],
                 truth_value: bool | None = None) -> None:
        self._evaluator = evaluator
        self._bound_generators = tuple(
            itertools.chain.from_iterable(expression._bound_generators
                                          for expression in expressions))
        self._bound_arity = len(self._bound_generators)
        self._free_arity = max(
            (expression._free_arity() for expression in expressions),
            default=0)

        unbound_expressions: 'list[icepool.expression.MultisetExpression[T_contra]]' = []
        prefix_start = 0
        for expression in expressions:
            unbound_expression, prefix_start = expression._unbind(
                prefix_start, len(self._bound_generators))
            unbound_expressions.append(unbound_expression)
        self._expressions = tuple(unbound_expressions)
        self._truth_value = truth_value

    def next_state(self, state, outcome, *counts):
        """Adjusts the counts, then forwards to inner."""
        if state is None:
            expression_states = (None, ) * len(self._expressions)
            evaluator_state = None
        else:
            expression_states, evaluator_state = state

        prefix_counts = counts[:len(self._evaluator.prefix_generators())]
        counts = counts[len(self._evaluator.prefix_generators()):]

        expression_states, expression_counts = zip(
            *(expression._next_state(expression_state, outcome, *counts)
              for expression, expression_state in zip(self._expressions,
                                                      expression_states)))
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
        expression_order = Order.merge(*(expression.order()
                                         for expression in self._expressions))
        return Order.merge(expression_order, self._evaluator.order())

    def extra_outcomes(self, *generators) -> Collection[T_contra]:
        """Forwards to inner."""
        return self._evaluator.extra_outcomes(*generators)

    @cached_property
    def _prefix_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._bound_generators + self._evaluator.prefix_generators()

    def prefix_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._prefix_generators

    def validate_arity(self, arity: int) -> None:
        if arity < self._free_arity:
            raise ValueError(
                f'Expected arity of {self._free_arity}, got {arity}.')

    def __bool__(self) -> bool:
        if self._truth_value is None:
            raise TypeError(
                'MultisetExpression only has a truth value if it is the result of the == or != operator.'
            )
        return self._truth_value

    def __str__(self) -> str:
        input_string = f'{self._bound_arity} bound, {self._free_arity} free'
        if len(self._expressions) == 1:
            expression_string = f'{self._expressions[0]}'
        else:
            expression_string = ', '.join(
                str(expression) for expression in self._expressions)
        output_string = str(self._evaluator)
        return f'Expression: {input_string} -> {expression_string} -> {output_string}'
