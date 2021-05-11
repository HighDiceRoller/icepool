import _context
import brute_force

from hdroller import Die
import numpy
import pytest

abs_tol = 1e-9

test_dice = [Die.d6, Die.d4.explode(1)]

def bf_repeat_and_sum(die, num_dice):
    return bf_keep_highest(die, num_dice, num_dice)

def bf_keep_highest(die, num_dice, num_keep):
    if num_keep == 0: return Die(0)
    counter = brute_force.BruteForceCounter()
    for rolls in numpy.ndindex((len(die),) * num_dice):
        total = sum(sorted(rolls)[-num_keep:]) + num_keep * die.min_outcome()
        mass = numpy.product(die.pmf()[numpy.array(rolls)])
        counter.insert(total, mass)
    return counter.die()
    
def bf_keep_lowest(die, num_dice, num_keep):
    if num_keep == 0: return Die(0)
    pmf_length = (len(die) - 1) * num_keep + 1
    counter = brute_force.BruteForceCounter()
    for rolls in numpy.ndindex((len(die),) * num_dice):
        total = sum(sorted(rolls)[:num_keep]) + num_keep * die.min_outcome()
        mass = numpy.product(die.pmf()[numpy.array(rolls)])
        counter.insert(total, mass)
    return counter.die()

def bf_keep_index(die, num_dice, index):
    counter = brute_force.BruteForceCounter()
    for rolls in numpy.ndindex((len(die),) * num_dice):
        picked = sorted(rolls)[index] + die.min_outcome()
        mass = numpy.product(die.pmf()[numpy.array(rolls)])
        counter.insert(picked, mass)
    return counter.die()

@pytest.mark.parametrize('num_dice', range(6))
@pytest.mark.parametrize('die', test_dice)
def test_repeat_and_sum(num_dice, die):
    result = die.repeat_and_sum(num_dice)
    expected = bf_repeat_and_sum(die, num_dice)
    assert result.ks_stat(expected) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('num_keep', range(6))
def test_keep_highest_of_5(die, num_keep):
    num_dice = 5

    result = die.keep_highest(num_dice, num_keep)
    expected = bf_keep_highest(die, num_dice, num_keep)

    assert result.ks_stat(expected) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('num_keep', range(6))
def test_keep_lowest_of_5(die, num_keep):
    num_dice = 5

    result = die.keep_lowest(num_dice, num_keep)
    expected = bf_keep_lowest(die, num_dice, num_keep)

    assert result.ks_stat(expected) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('index', range(5))
def test_keep_index_of_5(die, index):
    num_dice = 5
    
    result = die.keep_index(num_dice, index)
    expected = bf_keep_index(die, num_dice, index)

    assert result.ks_stat(expected) == pytest.approx(0.0, abs=abs_tol)
