__docformat__ = 'google'

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.order import Order, UnsupportedOrder

from abc import abstractmethod

from typing import Any, Literal


class LexiComparisonEvaluator(MultisetEvaluator[Any, int]):

    def initial_state(  # type: ignore
            self, order, outcomes, left_size, right_size, sort_order: Order,
            lexi_tuple: tuple[int, int, int, int, int]):
        # state: forward_order, extra, first, left_lead
        # positive on first/extra means the left side is earlier
        # first means the first differing element was paired with a later
        # element from the other side
        if order == sort_order:
            return True, 0, 0, 0
        else:
            if left_size is None or right_size is None:
                raise UnsupportedOrder(
                    'Reverse order not supported unless sizes of both operands are inferrable.'
                )
            extra = 0
            if left_size < right_size:
                extra = -1
            elif right_size < left_size:
                extra = 1
            return False, extra, 0, right_size - left_size

    def next_state(self, state, order, outcome, left, right):
        forward_order, extra, first, left_lead = state
        left = max(left, 0)
        right = max(right, 0)
        if forward_order:
            if extra == 0:
                if left < right:
                    extra = -1
                elif right < left:
                    extra = 1
            elif extra == 1 and right > 0:
                first = 1
            elif extra == -1 and left > 0:
                first = -1
        else:
            left_lead += left - right
            if left_lead > 0 and left > 0:
                first = -1
            elif left_lead < 0 and right > 0:
                first = 1
        return forward_order, extra, first, left_lead

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, left_size, right_size,
            sort_order: Order, lexi_tuple: tuple[int, int, int, int, int]):
        forward_order, extra, first, left_lead = final_state
        left_first, left_extra, tie, right_extra, right_first = lexi_tuple
        if first > 0:
            return left_first
        elif first < 0:
            return right_first
        elif extra > 0:
            return left_extra
        elif extra < 0:
            return right_extra
        else:
            return tie

    @property
    def next_state_key(self):
        return type(self)


lexi_comparison_evaluator = LexiComparisonEvaluator()
