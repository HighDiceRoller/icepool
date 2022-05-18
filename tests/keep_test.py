import _context

import icepool
import icepool.die.keep
import pytest

from icepool import d4, d6, d8, d10, d12

max_tuple_length = 5
max_num_values = 5

def bf_highest(die, num_dice, num_keep, num_drop=0):
    if num_keep == 0: return icepool.Die(0)
    def func(*outcomes):
        return sum(sorted(outcomes)[-(num_keep+num_drop):len(outcomes)-num_drop])
    return icepool.apply(func, *([die] * num_dice))
    
def bf_lowest(die, num_dice, num_keep, num_drop=0):
    if num_keep == 0: return icepool.Die(0)
    def func(*outcomes):
        return sum(sorted(outcomes)[num_drop:num_keep+num_drop])
    return icepool.apply(func, *([die] * num_dice))

def bf_keep(die, num_dice, keep_indexes):
    def func(*outcomes):
        return sorted(outcomes)[keep_indexes]
    return icepool.apply(func, *([die] * num_dice))

def bf_diff_highest_lowest(die, num_dice):
    def func(*outcomes):
        return max(outcomes) - min(outcomes)
    return icepool.apply(func, *([die] * num_dice))

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_highest(num_keep):
    die = icepool.d12
    result = die.highest(4, num_keep)
    expected = bf_highest(die, 4, num_keep)
    assert result.equals(expected)

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_highest_zero_weights(num_keep):
    die = icepool.Die(*range(6), weights=[0, 0, 1, 1, 1, 1])
    result = die.highest(4, num_keep).trim()
    expected = bf_highest(icepool.d4 + 1, 4, num_keep)
    assert result.equals(expected)

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_highest_drop_highest(num_keep):
    die = icepool.d12
    result = die.highest(4, num_keep, num_drop=1)
    expected = bf_highest(die, 4, num_keep, num_drop=1)
    assert result.equals(expected)

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_lowest(num_keep):
    die = icepool.d12
    result = die.lowest(4, num_keep)
    expected = bf_lowest(die, 4, num_keep)
    assert result.equals(expected)

@pytest.mark.parametrize('num_keep', range(1, 6))
def test_lowest_drop_highest(num_keep):
    die = icepool.d12
    result = die.lowest(4, num_keep, num_drop=1)
    expected = bf_lowest(die, 4, num_keep, num_drop=1)
    assert result.equals(expected)

@pytest.mark.parametrize('keep_index', range(0, 4))
def test_keep_index(keep_index):
    die = icepool.d12
    result = die.keep(4, count_dice=keep_index)
    expected = bf_keep(die, 4, keep_index)
    assert result.equals(expected)

def test_keep_all():
    die = icepool.d12
    result = die.keep(3)
    expected = 3 @ icepool.d12
    assert result.equals(expected)

def test_truncate_max():
    die = icepool.d12
    result = die.keep(truncate_max=[8, 6])
    expected = icepool.d8 + icepool.d6
    assert result.equals(expected)

def test_mixed_highest():
    die = icepool.d12
    result = die.highest(truncate_max=[8, 6, 4], num_keep=2)
    def func(*outcomes):
        return sum(sorted(outcomes)[-2:])
    expected = icepool.apply(func, icepool.d8, icepool.d6, icepool.d4)
    assert result.equals(expected)

def test_mixed_lowest():
    die = -icepool.d12
    result = -die.lowest(truncate_min=[-8, -6, -4], num_keep=2)
    def func(*outcomes):
        return sum(sorted(outcomes)[-2:])
    expected = icepool.apply(func, icepool.d8, icepool.d6, icepool.d4)
    assert result.equals(expected)

def test_pool_select():
    pool = icepool.Pool(icepool.d6, 5)
    assert pool[-2].equals(pool[-2:-1].sum())
    assert pool[-2:].count_dice() == (0, 0, 0, 1, 1)
    assert pool[-2:] == icepool.Pool(icepool.d6, 5, count_dice=slice(-2, None))

def test_sum_from_pool():
    pool = icepool.Pool(icepool.d6, 5)
    assert pool.sum().equals(5 @ icepool.d6)

def test_pool_select_multi():
    pool = icepool.Pool(icepool.d6)
    result = icepool.sum_pool.eval(pool[0,0,2,0,0])
    expected = 2 * icepool.d6.highest(5, 1, num_drop=2)
    assert result.equals(expected)

def test_pool_select_negative():
    pool = icepool.Pool(icepool.d6)
    result = icepool.sum_pool.eval(pool[0,0,-2,0,0])
    expected = -2 * icepool.d6.highest(5, 1, num_drop=2)
    assert result.equals(expected)

def test_pool_select_mixed_sign():
    pool = icepool.Pool(icepool.d6)
    result = icepool.sum_pool.eval(pool[-1,1])
    expected = abs(icepool.d6 - icepool.d6)
    assert result.equals(expected)

def test_pool_select_mixed_sign_split():
    pool = icepool.Pool(icepool.d6)
    result = icepool.sum_pool.eval(pool[-1,0,0,1])
    expected = bf_diff_highest_lowest(icepool.d6, 4)
    assert result.equals(expected)

def test_highest():
    result = icepool.highest(icepool.d6, icepool.d6)
    expected = icepool.d6.highest(2, 1)
    assert result.equals(expected)
    
def test_lowest():
    result = icepool.lowest(icepool.d6, icepool.d6)
    expected = icepool.d6.lowest(2, 1)
    assert result.equals(expected)

def test_common_truncation_identical():
    assert icepool.die.keep._common_truncation(d6, d6, d6) == (d6, {'num_dice' : 3})

def test_common_truncation_max():
    assert icepool.die.keep._common_truncation(d6, d8, d12) == (d12, {'truncate_max' : (6, 8, 12)})

def test_common_truncation_min():
    assert icepool.die.keep._common_truncation(-d6, -d8, -d12) == (-d12, {'truncate_min' : (-6, -8, -12)})

def test_common_truncation_mixed():
    assert icepool.die.keep._common_truncation(d6, d4 + 1) == (None, None)

def test_common_truncation_mixed2():
    assert icepool.die.keep._common_truncation(d6, d4, d4 + 2) == (None, None)

def test_common_truncation_mixed3():
    assert icepool.die.keep._common_truncation(-d6, d8, -d12) == (None, None)
