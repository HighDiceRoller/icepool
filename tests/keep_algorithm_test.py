import _context

import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, d20

test_dice = [
    (d6,),
    (icepool.Die(), d6, d6),
    (d6, d6, icepool.Die()),
    (d20, 10),
    (d6, d6, d6),
    (d4, d6, d8, d10),
    (-d4, -d4, -d6),
    (-d4, -d6, -d8, -d10),
    (d4+1, d6, d8, d10),
]

@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('num_keep', [0, 1, 2])
@pytest.mark.parametrize('num_drop', [0, 1, 2])
def test_lowest(dice, num_keep, num_drop):
    result = icepool.lowest(*dice, num_keep=num_keep, num_drop=num_drop)
    def expected_lowest(*outcomes):
        if num_keep == 0: return 0
        s = sorted(outcomes)
        start = num_drop
        stop = num_drop + num_keep
        return sum(s[start:stop])
    expected = icepool.apply(expected_lowest, *dice)
    assert result.equals(expected)

@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('num_keep', [0, 1, 2])
@pytest.mark.parametrize('num_drop', [0, 1, 2])
def test_highest(dice, num_keep, num_drop):
    result = icepool.highest(*dice, num_keep=num_keep, num_drop=num_drop)
    def expected_highest(*outcomes):
        if num_keep == 0: return 0
        s = sorted(outcomes)
        start = -(num_keep + num_drop) or None
        stop = -num_drop or None
        return sum(s[start:stop])
    expected = icepool.apply(expected_highest, *dice)
    assert result.equals(expected)
    
test_dice = [
    (),
    (d6,),
    (icepool.Die(), d6, d6),
    (d6, d6, icepool.Die()),
    (d20, 10),
    (d6, d6, d6),
    (d4, d6, d8, d10),
    (-d4, -d4, -d6),
    (-d4, -d6, -d8, -d10),
    (d4+1, d6, d8, d10),
]

@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('num_keep', [0, 1, 2])
@pytest.mark.parametrize('num_drop', [0, 1, 2])
def test_pool_lowest(dice, num_keep, num_drop):
    result = icepool.Pool(dice).lowest(num_keep=num_keep, num_drop=num_drop)
    def expected_lowest(*outcomes):
        if num_keep == 0: return 0
        s = sorted(outcomes)
        start = num_drop
        stop = num_drop + num_keep
        return sum(s[start:stop])
    expected = icepool.apply(expected_lowest, *dice)
    assert result.equals(expected)

@pytest.mark.parametrize('dice', test_dice)
@pytest.mark.parametrize('num_keep', [0, 1, 2])
@pytest.mark.parametrize('num_drop', [0, 1, 2])
def test_pool_highest(dice, num_keep, num_drop):
    result = icepool.Pool(dice).highest(num_keep=num_keep, num_drop=num_drop)
    def expected_highest(*outcomes):
        if num_keep == 0: return 0
        s = sorted(outcomes)
        start = -(num_keep + num_drop) or None
        stop = -num_drop or None
        return sum(s[start:stop])
    expected = icepool.apply(expected_highest, *dice)
    assert result.equals(expected)
