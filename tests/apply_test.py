import icepool
import pytest

from icepool import d6


def test_apply_reroll():
    result = icepool.apply(lambda x: icepool.Reroll if x > 4 else x, icepool.d6)
    expected = icepool.d4
    assert result.equals(expected)


def test_apply_die():
    result = icepool.apply(lambda x: icepool.d6 + x, icepool.d6)
    expected = 2 @ icepool.d6
    assert result.equals(expected)


def test_apply_sorted_max():
    result = icepool.apply_sorted(lambda x, y: y, icepool.d6, icepool.d6)
    expected = icepool.d6.sum_highest(2)
    assert result.equals(expected)


def test_apply_sorted_4d6kh3():
    result = icepool.apply_sorted[-3:]((lambda x, y, z: x + y + z), d6, d6, d6,
                                       d6)
    expected = icepool.d6.sum_highest(4, 3)
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
