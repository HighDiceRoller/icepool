import icepool
import pytest

from icepool import d4, d6, d8, d10, d12

test_pools = [
    icepool.standard_pool([4, 4]),
    icepool.standard_pool([6, 6, 6]),
    icepool.standard_pool([6, 6, 6, 6])[0, 0, 0, 1],
    icepool.standard_pool([6, 6, 6, 6])[0, 1, 1, 1],
    icepool.standard_pool([6, 6, 6, 6])[-1, 0, 0, 1],
    icepool.standard_pool([12, 10, 8, 6, 6, 4]),
    icepool.Pool([-d6, -d8, -d10]),
    (3 @ icepool.d6).pool(6)[-3:],
]


@pytest.mark.parametrize('pool', test_pools)
def test_unique_vs_expand(pool):
    if any(x < 0 for x in pool.keep_tuple()):
        pytest.skip()

    def unique(x):
        return tuple(sorted(set(x)))

    result = pool.unique().expand()
    expected = pool.expand().map(unique)
    assert result.equals(expected)


@pytest.mark.parametrize('pool', test_pools)
def test_unique_size(pool):
    if any(x < 0 for x in pool.keep_tuple()):
        pytest.skip()

    a = pool.unique().expand().map(len)
    b = pool.unique().size()
    assert a.equals(b)
