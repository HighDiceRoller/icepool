import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, d20

test_dice = [
    (d6,),
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
    result = icepool.lowest(*dice, keep=keep, drop=drop)

    def expected_lowest(*outcomes):
        if keep == 0:
            return 0
        s = sorted(outcomes)
        start = drop
        stop = drop + keep
        return sum(s[start:stop])

    expected = icepool.apply(expected_lowest, *dice)
    assert result.equals(expected)


@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('keep', [0, 1, 2])
@pytest.mark.parametrize('drop', [0, 1, 2])
def test_highest(dice, keep, drop):
    result = icepool.highest(*dice, keep=keep, drop=drop)

    def expected_highest(*outcomes):
        if keep == 0:
            return 0
        s = sorted(outcomes)
        start = -(keep + drop) or None
        stop = -drop or None
        return sum(s[start:stop])

    expected = icepool.apply(expected_highest, *dice)
    assert result.equals(expected)


test_dice = [
    (d6,),
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
def test_pool_lowest(dice, keep, drop):
    result = icepool.Pool(dice).sum_lowest(keep=keep, drop=drop)

    def expected_lowest(*outcomes):
        if keep == 0:
            return 0
        s = sorted(outcomes)
        start = drop
        stop = drop + keep
        return sum(s[start:stop])

    expected = icepool.apply(expected_lowest, *dice)
    assert result.equals(expected)


@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('keep', [0, 1, 2])
@pytest.mark.parametrize('drop', [0, 1, 2])
def test_pool_highest(dice, keep, drop):
    result = icepool.Pool(dice).sum_highest(keep=keep, drop=drop)

    def expected_highest(*outcomes):
        if keep == 0:
            return 0
        s = sorted(outcomes)
        start = -(keep + drop) or None
        stop = -drop or None
        return sum(s[start:stop])

    expected = icepool.apply(expected_highest, *dice)
    assert result.equals(expected)
