import icepool
import pytest

from icepool import d4, d6, d8, d10, d12

test_pools = [
    icepool.standard_pool([4, 4]),
    icepool.standard_pool([6, 6, 6]),
    icepool.standard_pool([6, 6, 6, 6])[0, 0, 0, 1],
    icepool.standard_pool([6, 6, 6, 6])[0, 1, 1, 1],
    icepool.standard_pool([6, 6, 6, 6])[-1, 0, 0, 1],
    icepool.standard_pool([12, 10, 8, 8, 6, 6, 6, 4]),
    icepool.Pool([-d6, -d8, -d10]),
    (3 @ icepool.d6).pool(12)[-6:],
]


@pytest.mark.parametrize('pool', test_pools)
def test_unique_vs_expand(pool):
    if any(x < 0 for x in pool.sorted_roll_counts()):
        pytest.skip()

    def unique(x):
        return tuple(sorted(set(x)))

    result = pool.expand(max_count=1)
    expected = pool.expand().map(unique)
    assert result.equals(expected)


@pytest.mark.parametrize('pool', test_pools)
def test_unique_count(pool):
    if any(x < 0 for x in pool.sorted_roll_counts()):
        pytest.skip()

    a = pool.expand(max_count=1).map(len)
    b = pool.count(max_count=1)
    assert a.equals(b)
