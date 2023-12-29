import icepool
import pytest

from icepool import d6


def test_explode_to_pool():
    assert d6.explode_to_pool(3, depth=4).sum() == 3 @ d6.explode(depth=4)


def test_map_to_pool():
    assert d6.pool(3).expand().map_to_pool().expand() == d6.pool(3).expand()
