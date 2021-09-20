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
    assert result.min_outcome() == expected.min_outcome()
    assert result.weights() == pytest.approx(expected.weights())

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_add(i, a):
    result = i + a
    expected = int_die_op(lambda x, y: x + y, i, a)
    assert result.min_outcome() == expected.min_outcome()
    assert result.weights() == pytest.approx(expected.weights())

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_add(a, b):
    result = a + b
    expected = die_die_op(lambda x, y: x + y, a, b)
    assert result.min_outcome() == expected.min_outcome()
    assert result.weights() == pytest.approx(expected.weights())
    
    
@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('i', range(-5, 5))
def test_die_int_sub(a, i):
    result = a - i
    expected = die_int_op(lambda x, y: x - y, a, i)
    assert result.min_outcome() == expected.min_outcome()
    assert result.weights() == pytest.approx(expected.weights())

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_sub(i, a):
    result = i - a
    expected = int_die_op(lambda x, y: x - y, i, a)
    assert result.min_outcome() == expected.min_outcome()
    assert result.weights() == pytest.approx(expected.weights())

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_sub(a, b):
    result = a - b
    expected = die_die_op(lambda x, y: x - y, a, b)
    assert result.min_outcome() == expected.min_outcome()
    assert result.weights() == pytest.approx(expected.weights())
    
def test_clip():
    result = Die.d6
    result = result.clip(2, 5)
    assert result.min_outcome() == 2
    assert result.weights() == pytest.approx([2, 1, 1, 2])

def test_abs_positive():
    result = Die.d6.abs()
    assert result.outcomes() == pytest.approx(Die.d6.outcomes())
    assert result.weights() == pytest.approx(Die.d6.weights())

def test_abs_negative():
    result = (-Die.d6).abs()
    assert result.outcomes() == pytest.approx(Die.d6.outcomes())
    assert result.weights() == pytest.approx(Die.d6.weights())

def test_abs_cross_zero():
    result = (Die.d6 - 3).abs()
    assert result.outcomes() == pytest.approx([0, 1, 2, 3])
    assert result.weights() == pytest.approx([1, 2, 2, 1])

def test_abs_cross_zero_nonuniform():
    result = (Die.d6 + Die.d6 - 7).abs()
    assert result.outcomes() == pytest.approx([0, 1, 2, 3, 4, 5])
    assert result.weights() == pytest.approx([6, 10, 8, 6, 4, 2])
