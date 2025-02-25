import icepool
import pytest

from icepool import MultisetEvaluator, Deck
from icepool.evaluator import LargestStraightEvaluator
from icepool.expression.multiset_expression import MultisetArityError

# no wraparound
best_run_evaluator = LargestStraightEvaluator()


class TrivialEvaluator(MultisetEvaluator):

    def next_state(self, state, outcome, *counts):
        return 0


class SumTupleEvaluator(MultisetEvaluator):

    def next_state(self, state, outcome, counts):
        if state is None:
            return tuple(0 for x in counts)
        else:
            return tuple(x + outcome * count
                         for x, count in zip(state, counts))


def test_empty_deal():
    deal = icepool.Deck(range(13), times=4).deal(())
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

    deal2 = deck.deal((5, 5))
    result2 = SumTupleEvaluator().evaluate(deal2)

    assert deal2.denominator() == result2.denominator()
    assert result1.equals(result2.marginals[0], simplify=True)
    assert result2.marginals[0].equals(result2.marginals[1])


def test_two_hand_sum_diff_size():
    deck = icepool.Deck(range(4), times=4)

    deal = deck.deal((2, 4))
    result = SumTupleEvaluator().evaluate(deal)

    assert deal.denominator() == result.denominator()
    assert (result.marginals[0] * 2).mean() == result.marginals[1].mean()


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


def test_append():
    base = Deck([1, 2, 2, 3, 3, 3])
    assert base.append(1) == Deck([1, 1, 2, 2, 3, 3, 3])
    assert base.append(0) == Deck([0, 1, 2, 2, 3, 3, 3])
    assert base.append(1, 3) == Deck([1, 1, 1, 1, 2, 2, 3, 3, 3])
    assert base.append(0, 3) == Deck([0, 0, 0, 1, 2, 2, 3, 3, 3])


def test_remove():
    base = Deck([1, 2, 2, 3, 3, 3])
    assert base.remove(0) == base
    assert base.remove(3) == Deck([1, 2, 2])
    assert base.remove(3, 1) == Deck([1, 2, 2, 3, 3])
    assert base.remove(1, 3) == Deck([2, 2, 3, 3, 3])
