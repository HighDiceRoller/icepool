import _context

import hdroller
import pytest

test_dice = [hdroller.d6, hdroller.d8, hdroller.d10.explode(2)]

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('i', range(-5, 5))
def test_die_int_add(a, i):
    result = a + i
    expected = hdroller.apply(lambda x, y: x + y, a, i)
    assert result.equals(expected)

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_add(i, a):
    result = i + a
    expected = hdroller.apply(lambda x, y: x + y, i, a)
    assert result.equals(expected)

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_add(a, b):
    result = a + b
    expected = hdroller.apply(lambda x, y: x + y, a, b)
    assert result.equals(expected)
    
@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('i', range(-5, 5))
def test_die_int_sub(a, i):
    result = a - i
    expected = hdroller.apply(lambda x, y: x - y, a, i)
    assert result.equals(expected)

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_sub(i, a):
    result = i - a
    expected = hdroller.apply(lambda x, y: x - y, i, a)
    assert result.equals(expected)

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_sub(a, b):
    result = a - b
    expected = hdroller.apply(lambda x, y: x - y, a, b)
    assert result.equals(expected)

"""
def test_clip():
    result = hdroller.d6
    result = result.clip(2, 5)
    expected = hdroller.die([2, 1, 1, 2], 2)
    assert result.equals(expected)
"""

def test_abs_positive():
    result = hdroller.d6.abs()
    expected = hdroller.d6
    assert result.equals(expected)

def test_abs_negative():
    result = (-hdroller.d6).abs()
    expected = hdroller.d6
    assert result.equals(expected)

def test_abs_cross_zero():
    result = (hdroller.d6 - 3).abs()
    expected = hdroller.die([1, 2, 2, 1], 0)
    assert result.equals(expected)

def test_abs_cross_zero_nonuniform():
    result = (hdroller.d6 + hdroller.d6 - 7).abs()
    expected = hdroller.die([6, 10, 8, 6, 4, 2], 0)
    assert result.equals(expected)

def test_mod():
    result = hdroller.d10 % 4
    expected = hdroller.die([2, 3, 3, 2], 0)
    assert result.equals(expected)
    
def test_div():
    result = hdroller.d10 // 4
    expected = hdroller.die([3, 4, 3], 0)
    assert result.equals(expected)

def test_reduce():
    result = hdroller.die([2, 4, 6], 0).reduce()
    expected = hdroller.die([1, 2, 3], 0)
    assert result.equals(expected)

def test_matmul_int_die():
    result = 2 @ hdroller.d6
    expected = hdroller.d6 + hdroller.d6
    assert result.equals(expected)

def test_matmul_die_die():
    result = hdroller.die(2) @ hdroller.d6
    expected = hdroller.d6 + hdroller.d6
    assert result.equals(expected)
