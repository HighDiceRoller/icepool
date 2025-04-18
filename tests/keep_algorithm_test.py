import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, d20, Order

test_dice = [
    (d6, ),
    (icepool.Die([]), d6, d6),
    (d6, d6, icepool.Die([])),
    (d20, 10),
    (d6, d6, d6),
    (d4, d6, d8, d10),
    (-d4, -d4, -d6),
    (-d4, -d6, -d8, -d10),
    (d4 + 1, d6, d8, d10),
]


@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('keep', [0, 1, 2])
@pytest.mark.parametrize('drop', [0, 1, 2])
def test_lowest(dice, keep, drop):
    result = icepool.lowest(dice, keep=keep, drop=drop)

    def expected_lowest(*outcomes):
        if keep == 0:
            return 0
        s = sorted(outcomes)
        start = drop
        stop = drop + keep
        return sum(s[start:stop])

    expected = icepool.map(expected_lowest, *dice, star=False)
    assert result.equals(expected)


@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('keep', [0, 1, 2])
@pytest.mark.parametrize('drop', [0, 1, 2])
def test_highest(dice, keep, drop):
    result = icepool.highest(dice, keep=keep, drop=drop)

    def expected_highest(*outcomes):
        if keep == 0:
            return 0
        s = sorted(outcomes)
        start = -(keep + drop) or None
        stop = -drop or None
        return sum(s[start:stop])

    expected = icepool.map(expected_highest, *dice, star=False)
    assert result.equals(expected)


test_dice = [
    (d6, ),
    (icepool.Die([]), d6, d6),
    (d6, d6, icepool.Die([])),
    (d20, 10),
    (d6, d6, d6),
    (d4, d6, d8, d10),
    (-d4, -d4, -d6),
    (-d4, -d6, -d8, -d10),
    (d4 + 1, d6, d8, d10),
]


@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('keep', [0, 1, 2])
@pytest.mark.parametrize('drop', [0, 1, 2])
@pytest.mark.parametrize('force_order', [Order.Ascending, Order.Descending])
def test_pool_lowest(dice, keep, drop, force_order):
    result = icepool.Pool(dice).lowest(
        keep=keep, drop=drop).force_order(force_order).sum()

    def expected_lowest(*outcomes):
        if keep == 0:
            return 0
        s = sorted(outcomes)
        start = drop
        stop = drop + keep
        return sum(s[start:stop])

    expected = icepool.map(expected_lowest, *dice, star=False)
    assert result.equals(expected)


@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('keep', [0, 1, 2])
@pytest.mark.parametrize('drop', [0, 1, 2])
@pytest.mark.parametrize('force_order', [Order.Ascending, Order.Descending])
def test_pool_highest(dice, keep, drop, force_order):
    result = icepool.Pool(dice).highest(
        keep=keep, drop=drop).force_order(force_order).sum()

    def expected_highest(*outcomes):
        if keep == 0:
            return 0
        s = sorted(outcomes)
        start = -(keep + drop) or None
        stop = -drop or None
        return sum(s[start:stop])

    expected = icepool.map(expected_highest, *dice, star=False)
    assert result.equals(expected)
