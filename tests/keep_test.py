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

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_highest(num_keep):
    die = hdroller.d12
    result = die.keep_highest(4, num_keep)
    expected = bf_keep_highest(die, 4, num_keep)
    assert result == expected

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_highest_zero_weights(num_keep):
    die = hdroller.die([0, 0, 1, 1, 1, 1], min_outcome=0, trim=True)
    result = die.keep_highest(4, num_keep)
    expected = bf_keep_highest(die, 4, num_keep)
    assert result == expected

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_highest_drop_highest(num_keep):
    die = hdroller.d12
    result = die.keep_highest(4, num_keep, num_drop=1)
    expected = bf_keep_highest(die, 4, num_keep, num_drop=1)
    assert result == expected

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_lowest(num_keep):
    die = hdroller.d12
    result = die.keep_lowest(4, num_keep)
    expected = bf_keep_lowest(die, 4, num_keep)
    assert result == expected

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_lowest_drop_highest(num_keep):
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
    result = die.keep(max_outcomes=[8, 6])
    expected = hdroller.d8 + hdroller.d6
    assert result == expected

def test_mixed_keep_highest():
    die = hdroller.d12
    result = die.keep_highest(max_outcomes=[8, 6, 4], num_keep=2)
    def func(*outcomes):
        return sum(sorted(outcomes)[-2:])
    expected = hdroller.apply(func, hdroller.d8, hdroller.d6, hdroller.d4)
    assert result == expected
    
def test_pool_select():
    pool = hdroller.pool(hdroller.d6, 5)
    assert pool[-2].select_dice() == (False, False, False, True, False)
    assert pool[-2:].select_dice() == (False, False, False, True, True)
    assert pool[-2:] == hdroller.pool(hdroller.d6, 5, select_dice=slice(-2, None))
    assert pool[-2:][:1] == pool[-2]

def test_pool_select_all():
    pool = hdroller.pool(hdroller.d6, 5)
    assert pool[-2].select_all_dice() == pool
