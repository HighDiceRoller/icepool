__docformat__ = 'google'

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.order import Order, UnsupportedOrder

from abc import abstractmethod

from typing import Any, Literal


class LexiComparisonEvaluator(MultisetEvaluator[Any, int]):

    def initial_state(  # type: ignore
            self, order, outcomes, left_size, right_size, sort_order: Order,
            lexi_tuple: tuple[int, int, int, int, int]):
        if order != sort_order:
            raise UnsupportedOrder()
        return 0

    def next_state(self, state, order, outcome, left, right):
        # States:
        # 1: left has unmatched extra element
        # 2: left has matched extra element
        # -1: right has unmatched extra element
        # -2: right has matched extra element
        if state == 0:
            if left < right:
                state = 1
            elif right < left:
                state = -1
        if state == 1 and right > 0:
            state = 2
        elif state == -1 and left > 0:
            state = -2
        return state

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, left_size, right_size,
            sort_order: Order, lexi_tuple: tuple[int, int, int, int, int]):
        return lexi_tuple[final_state]


lexi_comparison_evaluator = LexiComparisonEvaluator()
