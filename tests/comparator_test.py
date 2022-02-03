import _context

import hdroller
import pytest

def test_lt():
    result = hdroller.d6 < hdroller.d6
    expected = hdroller.bernoulli(15, 36)
    assert result.equals(expected)

def test_gt():
    result = hdroller.d6 > hdroller.d6
    expected = hdroller.bernoulli(15, 36)
    assert result.equals(expected)

def test_leq():
    result = hdroller.d6 <= hdroller.d6
    expected = hdroller.bernoulli(21, 36)
    assert result.equals(expected)

def test_geq():
    result = hdroller.d6 >= hdroller.d6
    expected = hdroller.bernoulli(21, 36)
    assert result.equals(expected)

def test_eq():
    result = hdroller.d6 == hdroller.d6
    expected = hdroller.bernoulli(6, 36)
    assert result.equals(expected)

def test_ne():
    result = hdroller.d6 != hdroller.d6
    expected = hdroller.bernoulli(30, 36)
    assert result.equals(expected)

def test_sign():
    result = (hdroller.d6 - 3).sign()
    expected = hdroller.die([2, 1, 3], min_outcome=-1)
    assert result.equals(expected)

def test_cmp():
    result = hdroller.d6.cmp(hdroller.d6 - 1)
    expected = hdroller.die([10, 5, 21], min_outcome=-1)
    assert result.equals(expected)

def test_weight_le():
    assert hdroller.d6.weight_le(3) == 3

def test_weight_lt():
    assert hdroller.d6.weight_lt(3) == 2
    
def test_weight_le_min():
    assert hdroller.d6.weight_le(1) == 1

def test_weight_lt_min():
    assert hdroller.d6.weight_lt(1) == 0

def test_weight_ge():
    assert hdroller.d6.weight_ge(3) == 4

def test_weight_gt():
    assert hdroller.d6.weight_gt(3) == 3

def test_weight_ge_max():
    assert hdroller.d6.weight_ge(6) == 1

def test_weight_gt_max():
    assert hdroller.d6.weight_gt(6) == 0

die_spaced = hdroller.die([1, 0, 0, 1, 0, 0, 1], min_outcome=-3)

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
