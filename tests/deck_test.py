import icepool
import pytest

from icepool import MultisetEvaluator
from icepool.evaluator import LargestStraightEvaluator

# no wraparound
best_run_evaluator = LargestStraightEvaluator()


class TrivialEvaluator(MultisetEvaluator):

    def next_state(self, state, outcome, *counts):
        return 0


class SumEachEvaluator(MultisetEvaluator):

    def next_state(self, state, outcome, *counts):
        if state is None:
            return tuple(0 for x in counts)
        else:
            return tuple(x + outcome * count for x, count in zip(state, counts))


def test_empty_deal():
    deal = icepool.Deck(range(13), times=4).deal()
    result = deal.evaluate(evaluator=TrivialEvaluator())
    assert result.equals(icepool.Die([0]))


def test_poker_straight():
    deal = icepool.Deck(range(13), times=4).deal(5)
    result = best_run_evaluator.evaluate(deal) == 5
    assert result.equals(icepool.coin(9216, 2598960))


def test_two_hand_sum_same_size():
    deck = icepool.Deck(range(4), times=4)
    deal1 = deck.deal(5)
    result1 = deal1.sum()

    deal2 = deck.deal(5, 5)
    result2 = deal2.evaluate(evaluator=SumEachEvaluator())

    assert deal2.denominator() == result2.denominator()
    assert result1.equals(result2.marginals[0], simplify=True)
    assert result2.marginals[0].equals(result2.marginals[1])


def test_two_hand_sum_diff_size():
    deck = icepool.Deck(range(4), times=4)

    deal = deck.deal(2, 4)
    result = deal.evaluate(evaluator=SumEachEvaluator())

    assert deal.denominator() == result.denominator()
    assert (result.marginals[0] * 2).mean() == result.marginals[1].mean()


def test_multiple_bind_error():
    deck = icepool.Deck(range(4), times=4)
    deal = deck.deal(2, 2)
    with pytest.raises(ValueError):
        deal.unique()
