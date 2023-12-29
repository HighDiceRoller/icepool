__docformat__ = 'google'

import icepool
from icepool.evaluator.multiset_evaluator import MultisetEvaluator

from abc import abstractmethod

from icepool.typing import Order
from typing import Any, Hashable, Literal


class CompairEvalautor(MultisetEvaluator[Any, int]):
    """Compares sorted pairs of two multisets and scores wins, ties, and extra elements.

    This can be used for e.g. RISK-like mechanics.
    """

    def __init__(self,
                 *,
                 order: Order = Order.Descending,
                 tie: int = 0,
                 left_greater: int = 0,
                 right_greater: int = 0):
        """Compares sorted pairs of two multisets and scores wins, ties, and extra elements.

        For example, `left=1` would count how many pairs were won by the left
        side, and `left=1, right=-1` would give the difference in the number of
        pairs won by each side.

        Args:
            order: If descending (default), pairs are made in descending order
                and the higher element wins. If ascending, pairs are made in
                ascending order and the lower element wins.
            
            tie: The score for each pair that is a tie.
            left: The score for each pair that left has a higher outcome.
            right: The score for each pair that right has a higher outcome.
        """
        if order == Order.Any:
            order = Order.Descending
        self._order = order

        self._tie = tie
        # Internally we find outcomes that were reached first.
        # For ascending order this results in a swap.
        if order < 0:
            self._left = left_greater
            self._right = right_greater
        else:
            self._left = right_greater
            self._right = left_greater

    def next_state(self, state, _, left, right):
        if left < 0 or right < 0:
            raise ValueError('Negative counts not supported.')
        # positive advantage favors left, negative favors right
        score, advantage = state or (0, 0)
        if advantage > 0:
            # How many left wins.
            wins = min(advantage, right)
            score += wins * self._left
            advantage -= wins
            right -= wins
        else:
            # How many right wins.
            wins = min(-advantage, left)
            score += wins * self._right
            advantage += wins
            left -= wins
        ties = min(left, right)
        score += ties * self._tie
        # Rest goes into advantage.
        advantage += left - right
        return score, advantage

    def final_outcome(self, final_state):
        score, advantage = final_state or (0, 0)
        return score

    def order(self) -> Order:
        return self._order
