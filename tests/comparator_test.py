import _context

import icepool
import pytest

def test_lt():
    result = icepool.d6 < icepool.d6
    expected = icepool.bernoulli(15, 36)
    assert result.equals(expected)

def test_gt():
    result = icepool.d6 > icepool.d6
    expected = icepool.bernoulli(15, 36)
    assert result.equals(expected)

def test_leq():
    result = icepool.d6 <= icepool.d6
    expected = icepool.bernoulli(21, 36)
    assert result.equals(expected)

def test_geq():
    result = icepool.d6 >= icepool.d6
    expected = icepool.bernoulli(21, 36)
    assert result.equals(expected)

def test_eq():
    result = icepool.d6 == icepool.d6
    expected = icepool.bernoulli(6, 36)
    assert result.equals(expected)

def test_ne():
    result = icepool.d6 != icepool.d6
    expected = icepool.bernoulli(30, 36)
    assert result.equals(expected)

def test_sign():
    result = (icepool.d6 - 3).sign()
    expected = icepool.Die(-1, 0, 1, weights=[2, 1, 3])
    assert result.equals(expected)

def test_cmp():
    result = icepool.d6.cmp(icepool.d6 - 1)
    expected = icepool.Die(-1, 0, 1, weights=[10, 5, 21])
    assert result.equals(expected)

def test_weight_le():
    assert icepool.d6.weight_le(3) == 3

def test_weight_lt():
    assert icepool.d6.weight_lt(3) == 2
    
def test_weight_le_min():
    assert icepool.d6.weight_le(1) == 1

def test_weight_lt_min():
    assert icepool.d6.weight_lt(1) == 0

def test_weight_ge():
    assert icepool.d6.weight_ge(3) == 4

def test_weight_gt():
    assert icepool.d6.weight_gt(3) == 3

def test_weight_ge_max():
    assert icepool.d6.weight_ge(6) == 1

def test_weight_gt_max():
    assert icepool.d6.weight_gt(6) == 0

die_spaced = icepool.Die(*range(-3, 4), weights=[1, 0, 0, 1, 0, 0, 1])

def test_weight_le_zero_weight():
    assert die_spaced.weight_le(-1) == 1
    assert die_spaced.weight_le(0) == 2
    assert die_spaced.weight_le(1) == 2

def test_weight_lt_zero_weight():
    assert die_spaced.weight_lt(-1) == 1
    assert die_spaced.weight_lt(0) == 1
    assert die_spaced.weight_lt(1) == 2
    
def test_weight_ge_zero_weight():
    assert die_spaced.weight_ge(-1) == 2
    assert die_spaced.weight_ge(0) == 2
    assert die_spaced.weight_ge(1) == 1

def test_weight_gt_zero_weight():
    assert die_spaced.weight_gt(-1) == 2
    assert die_spaced.weight_gt(0) == 1
    assert die_spaced.weight_gt(1) == 1

def test_nearest_le():
    assert icepool.d6.nearest_le(0) == None
    assert icepool.d6.nearest_le(1) == 1
    assert icepool.d6.nearest_le(6) == 6
    assert icepool.d6.nearest_le(7) == 6

def test_nearest_le_gap():
    die = icepool.Die(-3, 0, 3)
    assert die.nearest_le(-4) == None
    assert die.nearest_le(-3) == -3
    assert die.nearest_le(-2) == -3
    assert die.nearest_le(-1) == -3
    assert die.nearest_le(0) == 0
    assert die.nearest_le(1) == 0
    assert die.nearest_le(2) == 0
    assert die.nearest_le(3) == 3

def test_nearest_ge():
    assert icepool.d6.nearest_ge(0) == 1
    assert icepool.d6.nearest_ge(1) == 1
    assert icepool.d6.nearest_ge(6) == 6
    assert icepool.d6.nearest_ge(7) == None

def test_nearest_ge_gap():
    die = icepool.Die(-3, 0, 3)
    assert die.nearest_ge(-4) == -3
    assert die.nearest_ge(-3) == -3
    assert die.nearest_ge(-2) == 0
    assert die.nearest_ge(-1) == 0
    assert die.nearest_ge(0) == 0
    assert die.nearest_ge(1) == 3
    assert die.nearest_ge(2) == 3
    assert die.nearest_ge(3) == 3
    assert die.nearest_ge(4) == None

def test_highest():
    result = icepool.highest(icepool.d4+1, icepool.d6)
    expected = icepool.Die({2: 2, 3: 4, 4: 6, 5: 8, 6: 4})
    assert result.equals(expected)

def test_lowest():
    result = icepool.lowest(icepool.d4+1, icepool.d6)
    expected = icepool.Die({1: 4, 2: 8, 3: 6, 4: 4, 5: 2})
    assert result.equals(expected)