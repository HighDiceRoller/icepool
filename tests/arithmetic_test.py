import _context

import brute_force

from hdroller import Die
import pytest

test_dice = [Die.d6, Die.d8, Die.d10.explode(2)]

def die_int_op(f, a, i):
    counter = brute_force.BruteForceCounter()
    for outcome, mass in zip(a.outcomes(), a.pmf()):
        counter.insert(f(outcome, i), mass)
    return counter.die()

def int_die_op(f, i, a):
    counter = brute_force.BruteForceCounter()
    for outcome, mass in zip(a.outcomes(), a.pmf()):
        counter.insert(f(i, outcome), mass)
    return counter.die()

def die_die_op(f, a, b):    
    """
    Applies f to the outcomes of two dice.
    """
    counter = brute_force.BruteForceCounter()
    for outcome_a, mass_a in zip(a.outcomes(), a.pmf()):
        for outcome_b, mass_b in zip(b.outcomes(), b.pmf()):
            outcome = f(outcome_a, outcome_b)
            mass = mass_a * mass_b
            counter.insert(outcome, mass)
    return counter.die()

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('i', range(-5, 5))
def test_die_int_add(a, i):
    result = a + i
    expected = die_int_op(lambda x, y: x + y, a, i)
    assert result.ks_stat(expected) == pytest.approx(0.0)

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_add(i, a):
    result = i + a
    expected = int_die_op(lambda x, y: x + y, i, a)
    assert result.ks_stat(expected) == pytest.approx(0.0)

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_add(a, b):
    result = a + b
    expected = die_die_op(lambda x, y: x + y, a, b)
    assert result.ks_stat(expected) == pytest.approx(0.0)
    
    
@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('i', range(-5, 5))
def test_die_int_sub(a, i):
    result = a - i
    expected = die_int_op(lambda x, y: x - y, a, i)
    assert result.ks_stat(expected) == pytest.approx(0.0)

@pytest.mark.parametrize('i', range(-5, 5))
@pytest.mark.parametrize('a', test_dice)
def test_int_die_sub(i, a):
    result = i - a
    expected = int_die_op(lambda x, y: x - y, i, a)
    assert result.ks_stat(expected) == pytest.approx(0.0)

@pytest.mark.parametrize('a', test_dice)
@pytest.mark.parametrize('b', test_dice)
def test_die_die_sub(a, b):
    result = a - b
    expected = die_die_op(lambda x, y: x - y, a, b)
    assert result.ks_stat(expected) == pytest.approx(0.0)