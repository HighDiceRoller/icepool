import _context

import hdroller
import pytest

max_tuple_length = 5
max_num_values = 5

def bf_keep_highest(die, num_dice, num_keep, num_drop=0):
    if num_keep == 0: return hdroller.die(0)
    def func(*outcomes):
        return sum(sorted(outcomes)[-(num_keep+num_drop):len(outcomes)-num_drop])
    return hdroller.apply(func, *([die] * num_dice))
    
def bf_keep_lowest(die, num_dice, num_keep, num_drop=0):
    if num_keep == 0: return hdroller.die(0)
    def func(*outcomes):
        return sum(sorted(outcomes)[num_drop:num_keep+num_drop])
    return hdroller.apply(func, *([die] * num_dice))

def bf_keep(die, num_dice, keep_indexes):
    def func(*outcomes):
        return sorted(outcomes)[keep_indexes]
    return hdroller.apply(func, *([die] * num_dice))

@pytest.mark.parametrize('num_keep', range(1, 4))
def test_keep_highest(num_keep):
    die = hdroller.d12
    result = die.keep_highest(4, num_keep)
    expected = bf_keep_highest(die, 4, num_keep)
    assert result == expected

@pytest.mark.parametrize('num_keep', range(1, 4))
def test_keep_highest_mixed_drop_highest(num_keep):
    die = hdroller.d12
    result = die.keep_highest(4, num_keep, num_drop=1)
    expected = bf_keep_highest(die, 4, num_keep, num_drop=1)
    assert result == expected

@pytest.mark.parametrize('num_keep', range(1, 4))
def test_keep_lowest(num_keep):
    die = hdroller.d12
    result = die.keep_lowest(4, num_keep)
    expected = bf_keep_lowest(die, 4, num_keep)
    assert result == expected

@pytest.mark.parametrize('num_keep', range(1, 4))
def test_keep_lowest_mixed_drop_highest(num_keep):
    die = hdroller.d12
    result = die.keep_lowest(4, num_keep, num_drop=1)
    expected = bf_keep_lowest(die, 4, num_keep, num_drop=1)
    assert result == expected

@pytest.mark.parametrize('keep_index', range(0, 4))
def test_keep_index(keep_index):
    die = hdroller.d12
    result = die.keep(4, keep_index)
    expected = bf_keep(die, 4, keep_index)
    assert result == expected

def test_max_outcomes():
    die = hdroller.d12
    result = die.keep(2, max_outcomes=[8, 6])
    expected = hdroller.d8 + hdroller.d6
    assert result == expected
