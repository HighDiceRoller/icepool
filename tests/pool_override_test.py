import icepool
import pytest

from icepool import d6, Pool


def test_pool_merge():
    result = d6.pool(3) + d6.pool(3)
    expected = d6.pool(6)
    assert result == expected


def test_pool_cannot_merge():
    result = d6.pool(3)[:-1] + d6.pool(3)
    assert not isinstance(result, Pool)


def test_pool_multiply():
    result = d6.pool(4)[0, -1, 1, 1] * 2
    expected = d6.pool(4)[0, -2, 2, 2]
    assert result == expected
