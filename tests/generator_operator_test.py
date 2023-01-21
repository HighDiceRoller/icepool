import icepool
import pytest

from icepool import d6


def test_difference():
    result = (d6.pool(3) - d6.pool(1)).count()
    expected = icepool._highest_single(3 @ (d6 != 6), 2)
    assert result.simplify() == expected.simplify()


def test_intersection():
    result = (d6.pool(10) & {6: 5}).count()
    expected = icepool._lowest_single(10 @ (d6 == 6), 5)
    assert result == expected


def test_mul():
    result = (d6.pool(3) * 2).sum()
    expected = (3 @ d6) * 2
    assert result == expected


def test_multiple_union():
    result = d6.pool(1).union([6], [7]).sum()
    expected = d6 + 12
    assert result == expected


def test_multiple_intersection():
    result = d6.pool(1).intersection([d6], [d6]).sum()
    expected = (2 @ d6 == 12) * d6
    assert result == expected
