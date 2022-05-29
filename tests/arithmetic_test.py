import _context

import icepool
import pytest

test_dice = [icepool.d6, icepool.d8, icepool.d10.explode(max_depth=2)]

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('i', range(-5, 5))
def test_die_int_add(a, i):
    result = a + i
    expected = icepool.apply(lambda x, y: x + y, a, i)
    assert result.equals(expected)

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_add(i, a):
    result = i + a
    expected = icepool.apply(lambda x, y: x + y, i, a)
    assert result.equals(expected)

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_add(a, b):
    result = a + b
    expected = icepool.apply(lambda x, y: x + y, a, b)
    assert result.equals(expected)
    
@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('i', range(-5, 5))
def test_die_int_sub(a, i):
    result = a - i
    expected = icepool.apply(lambda x, y: x - y, a, i)
    assert result.equals(expected)

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_sub(i, a):
    result = i - a
    expected = icepool.apply(lambda x, y: x - y, i, a)
    assert result.equals(expected)

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_sub(a, b):
    result = a - b
    expected = icepool.apply(lambda x, y: x - y, a, b)
    assert result.equals(expected)

def test_clip():
    result = icepool.d6
    result = result.clip(2, 5)
    expected = icepool.Die(2, 2, 3, 4, 5, 5)
    assert result.equals(expected)

def test_clip_skip():
    result = icepool.d6 * 2
    result = result.clip(3, 9)
    expected = icepool.Die(3, 4, 6, 8, 9, 9)
    assert result.equals(expected)
    
def test_clip_outside():
    result = icepool.d6
    result = result.clip(0, 7)
    expected = icepool.Die(1, 2, 3, 4, 5, 6)
    assert result.equals(expected)

def test_truncate():
    result = icepool.d6
    result = result.truncate(2, 5)
    expected = icepool.Die(2, 3, 4, 5)
    assert result.equals(expected)

def test_truncate_outside():
    result = icepool.d6
    result = result.truncate(0, 7)
    expected = icepool.Die(1, 2, 3, 4, 5, 6)
    assert result.equals(expected)

def test_truncate_skip():
    result = icepool.d6 * 2
    result = result.truncate(3, 9)
    expected = icepool.Die(4, 6, 8)
    assert result.equals(expected)

def test_abs_positive():
    result = icepool.d6.abs()
    expected = icepool.d6
    assert result.equals(expected)

def test_abs_negative():
    result = (-icepool.d6).abs()
    expected = icepool.d6
    assert result.equals(expected)

def test_abs_cross_zero():
    result = (icepool.d6 - 3).abs()
    expected = icepool.Die(*range(4), weights=[1, 2, 2, 1])
    assert result.equals(expected)

def test_abs_cross_zero_nonuniform():
    result = (icepool.d6 + icepool.d6 - 7).abs()
    expected = icepool.Die(*range(6), weights=[6, 10, 8, 6, 4, 2])
    assert result.equals(expected)

def test_mod():
    result = icepool.d10 % 4
    expected = icepool.Die(*range(4), weights=[2, 3, 3, 2])
    assert result.equals(expected)
    
def test_div():
    result = icepool.d10 // 4
    expected = icepool.Die(*range(3), weights=[3, 4, 3])
    assert result.equals(expected)

def test_reduce():
    result = icepool.Die(*range(3), weights=[2, 4, 6]).reduce_weights()
    expected = icepool.Die(*range(3), weights=[1, 2, 3])
    assert result.equals(expected)

def test_matmul_int_die():
    result = 2 @ icepool.d6
    expected = icepool.d6 + icepool.d6
    assert result.equals(expected)

def test_matmul_die_die():
    result = icepool.Die(2) @ icepool.d6
    expected = icepool.d6 + icepool.d6
    assert result.equals(expected)

def test_d():
    result = icepool.d3 @ icepool.d(3)
    expected = icepool.Die({1: 9, 2: 12, 3: 16, 4: 12, 5: 12, 6: 10, 7: 6, 8: 3, 9: 1})
    assert result.equals(expected)

def test_d_negative():
    result = (icepool.d7 - 4) @ icepool.d(3)
    assert result.equals(-result)
