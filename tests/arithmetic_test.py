import _context

from hdroller import Die
import pytest

test_dice = [Die.d6, Die.d8, Die.d10.explode(2)]

def die_int_op(func, a, i):
    return Die.combine(a, i, func=func)

def int_die_op(func, i, a):
    return Die.combine(i, a, func=func)

def die_die_op(func, a, b):    
    """
    Applies func to the outcomes of two dice.
    """
    return Die.combine(a, b, func=func)

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('i', range(-5, 5))
def test_die_int_add(a, i):
    result = a + i
    expected = die_int_op(lambda x, y: x + y, a, i)
    assert result == expected

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_add(i, a):
    result = i + a
    expected = int_die_op(lambda x, y: x + y, i, a)
    assert result == expected

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_add(a, b):
    result = a + b
    expected = die_die_op(lambda x, y: x + y, a, b)
    assert result == expected
    
@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('i', range(-5, 5))
def test_die_int_sub(a, i):
    result = a - i
    expected = die_int_op(lambda x, y: x - y, a, i)
    assert result == expected

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_sub(i, a):
    result = i - a
    expected = int_die_op(lambda x, y: x - y, i, a)
    assert result == expected

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_sub(a, b):
    result = a - b
    expected = die_die_op(lambda x, y: x - y, a, b)
    assert result == expected
    
def test_clip():
    result = Die.d6
    result = result.clip(2, 5)
    expected = Die([2, 1, 1, 2], 2)
    assert result == expected

def test_abs_positive():
    result = Die.d6.abs()
    assert result == Die.d6

def test_abs_negative():
    result = (-Die.d6).abs()
    assert result == Die.d6

def test_abs_cross_zero():
    result = (Die.d6 - 3).abs()
    expected = Die([1, 2, 2, 1], 0)
    assert result == expected

def test_abs_cross_zero_nonuniform():
    result = (Die.d6 + Die.d6 - 7).abs()
    expected = Die([6, 10, 8, 6, 4, 2], 0)
    assert result == expected

def test_mod():
    result = Die.d10 % 4
    expected = Die([2, 3, 3, 2], 0)
    assert result == expected
    
def test_div():
    result = Die.d10 // 4
    expected = Die([3, 4, 3], 0)
    assert result == expected
