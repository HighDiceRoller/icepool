import icepool
import pytest


def test_reroll_default():
    result = icepool.d6.reroll()
    expected = icepool.d5 + 1
    assert result.equals(expected)


def test_reroll_bare():
    result = icepool.d6.reroll(1)
    expected = icepool.d5 + 1
    assert result.equals(expected)


def test_reroll_1():
    result = icepool.d6.reroll([1])
    expected = icepool.d5 + 1
    assert result.equals(expected)


def test_reroll_2():
    result = icepool.d6.reroll([1, 2])
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


def test_infinite_reroll():
    assert icepool.d4.reroll([1, 2, 3, 4]).is_empty()


def test_reroll_multidim():
    result = icepool.Die([(1, 0), (0, 1)]).reroll(lambda x: x[0] == 0)
    expected = icepool.Die([(1, 0)])
    assert result.equals(expected)


def test_reroll_until_multidim():
    result = icepool.Die([(1, 0), (0, 1)]).filter(lambda x: x[0] == 0)
    expected = icepool.Die([(0, 1)])
    assert result.equals(expected)
