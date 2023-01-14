__docformat__ = 'google'

import icepool.expression

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import Outcome

from typing import TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""


class ExpressionEvaluator(MultisetEvaluator[T_contra, int, U_co]):
    """Assigns an expression to be evaluated first to each input of an evaluator."""

    def __init__(self,
                 *expressions: 'icepool.expression.MultisetExpression',
                 evaluator: MultisetEvaluator[T_contra, int, U_co],
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

        expression_states, expression_counts = zip(
            *(expression.next_state(expression_state, outcome, *counts)
              for expression, expression_state in zip(self._expressions,
                                                      expression_states)))
        evaluator_state = self._evaluator.next_state(evaluator_state,
                                                     *expression_counts)
        return expression_states, evaluator_state

    def final_outcome(self, final_state):
        if final_state is None:
            return self._evaluator.final_outcome(None)
        else:
            _, evaluator_state = final_state
        return self._evaluator.final_outcome(evaluator_state)

    def order(self):
        """Forwards to inner."""
        return self._evaluator.order()

    def alignment(self, *generators):
        """Forwards to inner."""
        return self._evaluator.alignment(*generators)

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
                    self._evaluator)
