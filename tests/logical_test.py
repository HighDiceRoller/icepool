import icepool
import pytest

from fractions import Fraction


def test_invert():
    assert (~icepool.d6).mean() < 0


def test_and():
    assert (icepool.coin(1, 4) & icepool.coin(1, 4)).mean() == Fraction(1, 16)


def test_or():
    assert (icepool.coin(1, 4) | icepool.coin(1, 4)).mean() == Fraction(7, 16)


def test_xor():
    print(icepool.coin(1, 4) ^ icepool.coin(1, 4))
    print((icepool.coin(1, 4) ^ icepool.coin(1, 4)).probability(1))
    assert (icepool.coin(1, 4) ^ icepool.coin(1, 4)).mean() == Fraction(6, 16)


def test_ifelse():
    result = icepool.coin(1, 2).if_else(icepool.d8, icepool.d6).simplify()
    expected = icepool.Die(range(1, 9), times=[14, 14, 14, 14, 14, 14, 6,
                                               6]).simplify()
    assert result.equals(expected)
