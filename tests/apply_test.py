import icepool
import pytest

from icepool import d6, Pool, outcome_function, Again


def test_apply_reroll():
    result = icepool.apply(lambda x: icepool.Reroll if x > 4 else x, icepool.d6)
    expected = icepool.d4
    assert result.equals(expected)


def test_apply_die():
    result = icepool.apply(lambda x: icepool.d6 + x, icepool.d6)
    expected = 2 @ icepool.d6
    assert result.equals(expected)


def test_apply_pool():
    result = icepool.apply(lambda x: sum(x[-2:]), Pool([d6, d6, d6]))
    expected = icepool.d6.highest(3, 2)
    assert result.equals(expected)


def test_apply_no_dice():
    result = icepool.apply(lambda: 1)
    expected = icepool.Die({1: 1})
    assert result.equals(expected)


def test_reduce():
    dice = [icepool.d6] * 3
    result = icepool.reduce(lambda a, b: a + b, dice)
    expected = sum(dice)
    assert result.equals(expected)


def test_reduce_initial():
    dice = [icepool.d6] * 3
    result = icepool.reduce(lambda a, b: a + b, dice, initial=icepool.d6)
    expected = sum(dice) + icepool.d6
    assert result.equals(expected)


def test_accumulate():
    dice = [icepool.d6] * 3
    expected = icepool.Die([0])
    for result in icepool.accumulate(lambda a, b: a + b, dice):
        expected += icepool.d6
        assert result.equals(expected)


def test_accumulate_initial():
    dice = [icepool.d6] * 3
    expected = icepool.Die([0])
    for result in icepool.accumulate(lambda a, b: a + b,
                                     dice,
                                     initial=icepool.d6):
        expected += icepool.d6
        assert result.equals(expected)


def test_outcome_function():

    @outcome_function
    def explode_six(x):
        if x == 6:
            return 6 + Again()
        else:
            return x

    a = explode_six(d6, again_depth=2)

    @outcome_function(again_depth=2)
    def explode_six(x):
        if x == 6:
            return 6 + Again()
        else:
            return x

    b = explode_six(d6)

    assert a == d6.explode(depth=2)
    assert b == d6.explode(depth=2)


def test_expression_to_outcome_function():

    @outcome_function
    def test(x):
        return sum(x)

    assert test(d6.pool(3) - d6.pool(3)) == (d6.pool(3) - d6.pool(3)).sum()
