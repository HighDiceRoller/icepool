import _context

import hdroller
import pytest

max_tuple_length = 5
max_num_values = 5

def bf_keep_highest(die, num_dice, num_keep, num_drop=0):
    if num_keep == 0: return hdroller.Die(0)
    def func(*outcomes):
        return sum(sorted(outcomes)[-(num_keep+num_drop):len(outcomes)-num_drop])
    return hdroller.apply(func, *([die] * num_dice))
    
def bf_keep_lowest(die, num_dice, num_keep, num_drop=0):
    if num_keep == 0: return hdroller.Die(0)
    def func(*outcomes):
        return sum(sorted(outcomes)[num_drop:num_keep+num_drop])
    return hdroller.apply(func, *([die] * num_dice))

def bf_keep(die, num_dice, keep_indexes):
    def func(*outcomes):
        return sorted(outcomes)[keep_indexes]
    return hdroller.apply(func, *([die] * num_dice))

def bf_diff_highest_lowest(die, num_dice):
    def func(*outcomes):
        return max(outcomes) - min(outcomes)
    return hdroller.apply(func, *([die] * num_dice))

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_highest(num_keep):
    die = hdroller.d12
    result = die.keep_highest(4, num_keep)
    expected = bf_keep_highest(die, 4, num_keep)
    assert result.equals(expected)

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_highest_zero_weights(num_keep):
    die = hdroller.Die([0, 0, 1, 1, 1, 1], min_outcome=0)
    result = die.keep_highest(4, num_keep).trim()
    expected = bf_keep_highest(hdroller.d4 + 1, 4, num_keep)
    assert result.equals(expected)

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_highest_drop_highest(num_keep):
    die = hdroller.d12
    result = die.keep_highest(4, num_keep, num_drop=1)
    expected = bf_keep_highest(die, 4, num_keep, num_drop=1)
    assert result.equals(expected)

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_lowest(num_keep):
    die = hdroller.d12
    result = die.keep_lowest(4, num_keep)
    expected = bf_keep_lowest(die, 4, num_keep)
    assert result.equals(expected)

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_keep_lowest_drop_highest(num_keep):
    die = hdroller.d12
    result = die.keep_lowest(4, num_keep, num_drop=1)
    expected = bf_keep_lowest(die, 4, num_keep, num_drop=1)
    assert result.equals(expected)

@pytest.mark.parametrize('keep_index', range(0, 4))
def test_keep_index(keep_index):
    die = hdroller.d12
    result = die.keep(4, keep_index)
    expected = bf_keep(die, 4, keep_index)
    assert result.equals(expected)

def test_max_outcomes():
    die = hdroller.d12
    result = die.keep(max_outcomes=[8, 6])
    expected = hdroller.d8 + hdroller.d6
    assert result.equals(expected)

def test_mixed_keep_highest():
    die = hdroller.d12
    result = die.keep_highest(max_outcomes=[8, 6, 4], num_keep=2)
    def func(*outcomes):
        return sum(sorted(outcomes)[-2:])
    expected = hdroller.apply(func, hdroller.d8, hdroller.d6, hdroller.d4)
    assert result.equals(expected)
    
def test_pool_select():
    pool = hdroller.Pool(hdroller.d6, 5)
    assert pool[-2].count_dice() == (0, 0, 0, 1, 0)
    assert pool[-2:].count_dice() == (0, 0, 0, 1, 1)
    assert pool[-2:] == hdroller.Pool(hdroller.d6, 5, count_dice=slice(-2, None))

def test_pool_select_multi():
    pool = hdroller.Pool(hdroller.d6)
    result = hdroller.pool_sum.eval(pool[0,0,2,0,0])
    expected = 2 * hdroller.d6.keep_highest(5, 1, num_drop=2)
    assert result.equals(expected)

def test_pool_select_negative():
    pool = hdroller.Pool(hdroller.d6)
    result = hdroller.pool_sum.eval(pool[0,0,-2,0,0])
    expected = -2 * hdroller.d6.keep_highest(5, 1, num_drop=2)
    assert result.equals(expected)

def test_pool_select_mixed_sign():
    pool = hdroller.Pool(hdroller.d6)
    result = hdroller.pool_sum.eval(pool[-1,1])
    expected = abs(hdroller.d6 - hdroller.d6)
    assert result.equals(expected)

def test_pool_select_mixed_sign_split():
    pool = hdroller.Pool(hdroller.d6)
    result = hdroller.pool_sum.eval(pool[-1,0,0,1])
    expected = bf_diff_highest_lowest(hdroller.d6, 4)
    assert result.equals(expected)
