__docformat__ = 'google'

import icepool

from icepool.evaluator.multiset_evaluator import MultisetEvaluator

from icepool.typing import Outcome, Order, T_contra, U_co
from typing import Any


class ConstantEvaluator(MultisetEvaluator[Any, U_co]):
    """An evaluator that ignores its arguments and returns a constant result."""

    def __init__(self, result: 'icepool.Die[U_co]') -> None:
        self._result = result

    def next_state(self, state, outcome, *counts):
        return None

    def final_outcome(self, final_state) -> 'icepool.Die[U_co]':
        return self._result
