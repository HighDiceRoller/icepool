import icepool
import pytest

from icepool import MultisetEvaluator, Deck
from icepool.evaluator import LargestStraightEvaluator
from icepool.multiset_expression import MultisetArityError

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
            return tuple(x + outcome * count
                         for x, count in zip(state, counts))


def test_empty_deal():
    deal = icepool.Deck(range(13), times=4).deal()
    result = TrivialEvaluator().evaluate(deal)
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
    result2 = SumEachEvaluator().evaluate(deal2)

    assert deal2.denominator() == result2.denominator()
    assert result1.equals(result2.marginals[0], simplify=True)
    assert result2.marginals[0].equals(result2.marginals[1])


def test_two_hand_sum_diff_size():
    deck = icepool.Deck(range(4), times=4)

    deal = deck.deal(2, 4)
    result = SumEachEvaluator().evaluate(deal)

    assert deal.denominator() == result.denominator()
    assert (result.marginals[0] * 2).mean() == result.marginals[1].mean()


def test_multiple_bind_error():
    deck = icepool.Deck(range(4), times=4)
    deal = deck.deal(2, 2)
    with pytest.raises(MultisetArityError):
        deal.unique().count()


def test_add():
    deck = Deck([1, 2, 3]) + Deck([3, 4])
    assert deck == Deck([1, 2, 3, 3, 4])


def test_sub():
    deck = Deck([1, 2, 3]) - Deck([3, 4])
    assert deck == Deck([1, 2])


def test_and():
    deck = Deck([1, 2, 3]) & Deck([3, 4])
    assert deck == Deck([3])


def test_or():
    deck = Deck([1, 2, 3]) | Deck([3, 4])
    assert deck == Deck([1, 2, 3, 4])


def test_mul():
    deck = Deck([1, 2, 3]) * 2
    assert deck == Deck([1, 1, 2, 2, 3, 3])


def test_floordiv():
    deck = Deck([1, 1, 1, 2, 2, 3]) // 2
    assert deck == Deck([1, 2])


def test_highest():
    deck = Deck(range(10))
    result = deck.deal(4).highest(2).expand().simplify()
    expected = deck.deal(4).expand().map(lambda x: x[2:]).simplify()
    assert result == expected


def test_lowest():
    deck = Deck(range(10))
    result = deck.deal(4).lowest(2).expand().simplify()
    expected = deck.deal(4).expand().map(lambda x: x[:-2]).simplify()
    assert result == expected
