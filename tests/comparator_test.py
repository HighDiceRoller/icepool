import _context

import icepool
import pytest

def test_lt():
    result = icepool.d6 < icepool.d6
    expected = icepool.bernoulli(15, 36)
    assert result.equals(expected)

def test_lt_fixed():
    assert (icepool.d6 < 1).mean() == 0.0
    assert (icepool.d6 < 7).mean() == 1.0

def test_gt():
    result = icepool.d6 > icepool.d6
    expected = icepool.bernoulli(15, 36)
    assert result.equals(expected)
    
def test_gt_fixed():
    assert (icepool.d6 > 0).mean() == 1.0
    assert (icepool.d6 > 6).mean() == 0.0

def test_leq():
    result = icepool.d6 <= icepool.d6
    expected = icepool.bernoulli(21, 36)
    assert result.equals(expected)
    
def test_leq_fixed():
    assert (icepool.d6 <= 0).mean() == 0.0
    assert (icepool.d6 <= 6).mean() == 1.0

def test_geq():
    result = icepool.d6 >= icepool.d6
    expected = icepool.bernoulli(21, 36)
    assert result.equals(expected)
    
def test_geq_fixed():
    assert (icepool.d6 >= 1).mean() == 1.0
    assert (icepool.d6 >= 7).mean() == 0.0

def test_eq():
    result = icepool.d6 == icepool.d6
    expected = icepool.bernoulli(6, 36)
    assert result.equals(expected)

def test_eq_fixed():
    assert (icepool.d6 == 1).equals(icepool.coin(1, 6))
    assert (icepool.d6 == 6).equals(icepool.coin(1, 6))

def test_ne():
    result = icepool.d6 != icepool.d6
    expected = icepool.bernoulli(30, 36)
    assert result.equals(expected)

def test_ne_fixed():
    assert (icepool.d6 != 1).equals(icepool.coin(5, 6))
    assert (icepool.d6 != 6).equals(icepool.coin(5, 6))

def test_sign():
    result = (icepool.d6 - 3).sign()
    expected = icepool.Die({-1:2, 0:1, 1:3})
    assert result.equals(expected)

def test_cmp():
    result = icepool.d6.cmp(icepool.d6 - 1)
    expected = icepool.Die({-1:10, 0:5, 1:21})
    assert result.equals(expected)

def test_quantity_le():
    assert icepool.d6.quantity_le(3) == 3

def test_quantity_lt():
    assert icepool.d6.quantity_lt(3) == 2
    
def test_quantity_le_min():
    assert icepool.d6.quantity_le(1) == 1

def test_quantity_lt_min():
    assert icepool.d6.quantity_lt(1) == 0

def test_quantity_ge():
    assert icepool.d6.quantity_ge(3) == 4

def test_quantity_gt():
    assert icepool.d6.quantity_gt(3) == 3

def test_quantity_ge_max():
    assert icepool.d6.quantity_ge(6) == 1

def test_quantity_gt_max():
    assert icepool.d6.quantity_gt(6) == 0

die_spaced = icepool.Die(range(-3, 4), times=[1, 0, 0, 1, 0, 0, 1])

def test_quantity_le_zero_weight():
    assert die_spaced.quantity_le(-1) == 1
    assert die_spaced.quantity_le(0) == 2
    assert die_spaced.quantity_le(1) == 2

def test_quantity_lt_zero_weight():
    assert die_spaced.quantity_lt(-1) == 1
    assert die_spaced.quantity_lt(0) == 1
    assert die_spaced.quantity_lt(1) == 2
    
def test_quantity_ge_zero_weight():
    assert die_spaced.quantity_ge(-1) == 2
    assert die_spaced.quantity_ge(0) == 2
    assert die_spaced.quantity_ge(1) == 1

def test_quantity_gt_zero_weight():
    assert die_spaced.quantity_gt(-1) == 2
    assert die_spaced.quantity_gt(0) == 1
    assert die_spaced.quantity_gt(1) == 1

def test_nearest_le():
    assert icepool.d6.nearest_le(0) == None
    assert icepool.d6.nearest_le(1) == 1
    assert icepool.d6.nearest_le(6) == 6
    assert icepool.d6.nearest_le(7) == 6

def test_nearest_le_gap():
    die = icepool.Die([-3, 0, 3])
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
    die = icepool.Die([-3, 0, 3])
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