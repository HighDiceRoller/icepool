__docformat__ = 'google'

import icepool.expression

from icepool.evaluator.outcome_count_evaluator import MultisetEvaluator
from icepool.typing import Outcome

from typing import TypeVar

T_contra = TypeVar('T_contra', bound=Outcome, contravariant=True)
"""Type variable representing the input outcome type."""

U_co = TypeVar('U_co', bound=Outcome, covariant=True)
"""Type variable representing the final outcome type."""


class ExpressionEvaluator(MultisetEvaluator[T_contra, int, U_co]):

    def __init__(self, *expressions: 'icepool.expression.MultisetExpression',
                 evaluator: MultisetEvaluator[T_contra, int, U_co]) -> None:
        self._evaluator = evaluator
        self._expressions = expressions

    def next_state(self, state, outcome, *counts):
        """Adjusts the counts, then forwards to inner."""
        counts = (expression.evaluate_counts(outcome, counts)
                  for expression in self._expressions)
        return self._evaluator.next_state(state, outcome, *counts)

    def final_outcome(self, final_state, *generators):
        """Forwards to inner."""
        return self._evaluator.final_outcome(final_state, *generators)

    def order(self, *generators):
        """Forwards to inner."""
        return self._evaluator.order(*generators)

    def alignment(self, *generators):
        """Forwards to inner."""
        return self._evaluator.alignment(*generators)
