import icepool
import pytest

from icepool import d6


def test_difference():
    result = (d6.pool(3) - d6.pool(1)).count()
    expected = icepool.highest(3 @ (d6 != 6), 2)
    assert result.simplify() == expected.simplify()


def test_intersection():
    result = (d6.pool(10) & {6: 5}).count()
    expected = icepool.lowest(10 @ (d6 == 6), 5)
    assert result == expected
