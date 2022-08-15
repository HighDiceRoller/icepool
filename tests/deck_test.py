import icepool
import pytest

from icepool import BestRunEvaluator

# no wraparound
find_best_run = BestRunEvaluator()


def trivial_next_state(state, outcome, *counts):
    return 0


def sum_each(state, outcome, *counts):
    if state is None:
        return tuple(0 for x in counts)
    else:
        return tuple(x + outcome * count for x, count in zip(state, counts))


def test_empty_deal():
    deal = icepool.Deck(range(13), times=4).deal()
    result = deal.evaluate(trivial_next_state)
    assert result.equals(icepool.Die([0]))


def test_poker_straight():
    deal = icepool.Deck(range(13), times=4).deal(5)
    result = find_best_run.evaluate(deal).marginals[0] == 5
    assert result.equals(icepool.coin(9216, 2598960))


def test_two_hand_sum_same_size():
    deck = icepool.Deck(range(4), times=4)
    deal1 = deck.deal(5)
    result1 = deal1.sum()

    deal2 = deck.deal(5, 5)
    result2 = deal2.evaluate(sum_each)

    assert deal2.denominator() == result2.denominator()
    assert result1.equals(result2.marginals[0], simplify=True)
    assert result2.marginals[0].equals(result2.marginals[1])


def test_two_hand_sum_diff_size():
    deck = icepool.Deck(range(4), times=4)

    deal = deck.deal(2, 4)
    result = deal.evaluate(sum_each)

    assert deal.denominator() == result.denominator()
    assert (result.marginals[0] * 2).mean() == result.marginals[1].mean()
