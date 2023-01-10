__docformat__ = 'google'

import icepool.expression

from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator
from icepool.typing import Outcome

from typing import TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""


class ExpressionEvaluator(OutcomeCountEvaluator[T_contra, tuple[int, ...],
                                                U_co]):

    def __init__(self, expression: 'icepool.expression.MultisetExpression',
                 evaluator: OutcomeCountEvaluator[T_contra, int, U_co]) -> None:
        self._expression = expression
        self._evaluator = evaluator

    def next_state(self, state, outcome, *counts):
        """Adjusts the count, then forwards to inner."""
        count = self._expression.evaluate(outcome, *counts)
        return self._evaluator.next_state(state, outcome, count)

    def final_outcome(self, final_state, *generators):
        """Forwards to inner."""
        return self._inner.final_outcome(final_state, *generators)

    def order(self, *generators):
        """Forwards to inner."""
        return self._inner.order(*generators)

    def alignment(self, *generators):
        """Forwards to inner."""
        return self._inner.alignment(*generators)
