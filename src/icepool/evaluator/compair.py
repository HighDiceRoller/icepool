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
                 initial=None,
                 tie=None,
                 left=None,
                 right=None,
                 extra_left=None,
                 extra_right=None,
                 order: Order = Order.Descending):
        """Compares sorted pairs of two multisets and scores wins, ties, and extra elements.

        For example, `left=1` would count how many pairs were won by the left
        side, and `left=1, right=-1` would give the difference in the number of
        pairs won by each side.

        Any score argument not provided will be set to a zero value determined 
        from another score argument times `0`.

        Args:
            initial: The initial score.
            tie: The score for each pair that is a tie.
            left: The score for each pair that left wins.
            right: The score for each pair that right wins.
            extra_left: If left has more elements, each extra element scores
                this much.
            extra_right: If right has more elements, each extra element scores
                this much.
            
            order: If descending (default), pairs are made in descending order
                and the higher element wins. If ascending, pairs are made in
                ascending order and the lower element wins.
        """
        all_scores = (tie, left, right, extra_left, extra_right, initial)
        default_score = None
        if None in all_scores:
            for score in all_scores:
                if score is not None:
                    default_score = score * 0
                    break
            else:
                raise TypeError('At least one score must be provided.')

        self._left = left if left is not None else default_score
        self._tie = tie if tie is not None else default_score
        self._right = right if right is not None else default_score
        self._extra_left = extra_left if extra_left is not None else default_score
        self._extra_right = extra_right if extra_right is not None else default_score
        self._initial = initial if initial is not None else default_score

        self._order = order

    def next_state(self, state, _, left, right):
        if left < 0 or right < 0:
            raise ValueError('Negative counts not supported.')
        # positive advantage favors left, negative favors right
        score, advantage = state or (self._initial, 0)
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
        score, advantage = final_state or (self._initial, 0)
        if advantage > 0:
            score += advantage * self._extra_left
        elif advantage < 0:
            score -= advantage * self._extra_right
        return score

    def order(self) -> Order:
        return self._order
