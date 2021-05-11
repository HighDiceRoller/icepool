import _context
import brute_force

from hdroller import Die
import numpy
import pytest

abs_tol = 1e-9

test_dice = [Die.d6, Die.d4.explode(1)]

@pytest.mark.parametrize('num_dice', range(6))
@pytest.mark.parametrize('die', test_dice)
def test_repeat_and_sum(num_dice, die):
    result = die.repeat_and_sum(num_dice)
    expected = brute_force.repeat_and_sum(die, num_dice)
    assert result.ks_stat(expected) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('num_keep', range(6))
def test_keep_highest_of_5(die, num_keep):
    num_dice = 5

    result = die.keep_highest(num_dice, num_keep)
    expected = brute_force.keep_highest(die, num_dice, num_keep)

    assert result.ks_stat(expected) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('num_keep', range(6))
def test_keep_lowest_of_5(die, num_keep):
    num_dice = 5

    result = die.keep_lowest(num_dice, num_keep)
    expected = brute_force.keep_lowest(die, num_dice, num_keep)

    assert result.ks_stat(expected) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('die', test_dice)
@pytest.mark.parametrize('index', range(5))
def test_keep_index_of_5(die, index):
    num_dice = 5
    
    result = die.keep_index(num_dice, index)
    expected = brute_force.keep_index(die, num_dice, index)

    assert result.ks_stat(expected) == pytest.approx(0.0, abs=abs_tol)
