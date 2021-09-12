import _context

import brute_force

from hdroller import Die
import pytest

test_dice = [Die.d6, Die.d8, Die.d10.explode(2)]

def die_int_op(f, a, i):
    counter = brute_force.BruteForceCounter()
    for outcome, weight in zip(a.outcomes(), a.weights()):
        counter.insert(f(outcome, i), weight)
    return counter.die()

def int_die_op(f, i, a):
    counter = brute_force.BruteForceCounter()
    for outcome, weight in zip(a.outcomes(), a.weights()):
        counter.insert(f(i, outcome), weight)
    return counter.die()

def die_die_op(f, a, b):    
    """
    Applies f to the outcomes of two dice.
    """
    counter = brute_force.BruteForceCounter()
    for outcome_a, weight_a in zip(a.outcomes(), a.weights()):
        for outcome_b, weight_b in zip(b.outcomes(), b.weights()):
            outcome = f(outcome_a, outcome_b)
            weight = weight_a * weight_b
            counter.insert(outcome, weight)
    return counter.die()

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
