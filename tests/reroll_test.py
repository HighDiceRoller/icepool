import icepool
import pytest


def test_reroll_default():
    result = icepool.d6.reroll(depth='inf')
    expected = icepool.d5 + 1
    assert result.equals(expected)


def test_reroll_1():
    result = icepool.d6.reroll([1], depth='inf')
    expected = icepool.d5 + 1
    assert result.equals(expected)


def test_reroll_2():
    result = icepool.d6.reroll([1, 2], depth='inf')
    expected = icepool.d4 + 2
    assert result.equals(expected)


def test_reroll_limit():
    result = icepool.d4.reroll([1], depth=1)
    expected = icepool.Die(range(1, 5), times=[1, 5, 5, 5])
    assert result.equals(expected)


def test_reroll_until_limit():
    result = icepool.d4.filter([2, 3, 4], depth=1)
    expected = icepool.Die(range(1, 5), times=[1, 5, 5, 5])
    assert result.equals(expected)


def test_reroll_func():
    result = icepool.d4.reroll(lambda x: x == 1, depth=1)
    expected = icepool.Die(range(1, 5), times=[1, 5, 5, 5])
    assert result.equals(expected)


def test_reroll_until_func():
    result = icepool.d4.filter(lambda x: x != 1, depth=1)
    expected = icepool.Die(range(1, 5), times=[1, 5, 5, 5])
    assert result.equals(expected)


def test_reroll_depth_0():
    assert icepool.d4.reroll(depth=0) == icepool.d4


def test_reroll_depth_3():
    result = icepool.d4.reroll(depth=3)
    expected = icepool.d4.reroll(depth=1).reroll(depth=1)
    assert result.equals(expected)


def test_reroll_depth_3_mixed():
    die = 2 @ icepool.d6
    result = die.reroll([2, 3], depth=3)
    expected = die.reroll([2, 3], depth=1).reroll([2, 3], depth=1)
    assert result.equals(expected)


def test_infinite_reroll():
    assert icepool.d4.reroll([1, 2, 3, 4], depth='inf').is_empty()


def test_reroll_multidim():
    result = icepool.Die([(1, 0), (0, 1)]).reroll(lambda x: x[0] == 0,
                                                  depth='inf')
    expected = icepool.Die([(1, 0)])
    assert result.equals(expected)


def test_reroll_until_multidim():
    result = icepool.Die([(1, 0), (0, 1)]).filter(lambda x: x[0] == 0,
                                                  depth='inf')
    expected = icepool.Die([(0, 1)])
    assert result.equals(expected)
