import _context
import brute_force

from hdroller import Die
import hdroller.die_sort
import pytest

import numpy

max_tuple_length = 5
max_num_values = 5

def bf_keep_highest(num_keep, *dice):
    if num_keep == 0: return Die(0)
    counter = brute_force.BruteForceCounter()
    shape = tuple(len(die) for die in dice)
    min_outcome = sum(sorted(die.min_outcome() for die in dice)[-num_keep:])
    for rolls in numpy.ndindex(shape):
        total = sum(sorted(rolls)[-num_keep:]) + min_outcome
        mass = numpy.product([die.pmf()[roll] for die, roll in zip(dice, rolls)])
        counter.insert(total, mass)
    return counter.die()
    
def bf_keep_lowest(num_keep, *dice):
    if num_keep == 0: return Die(0)
    counter = brute_force.BruteForceCounter()
    shape = tuple(len(die) for die in dice)
    min_outcome = sum(sorted(die.min_outcome() for die in dice)[:num_keep])
    for rolls in numpy.ndindex(shape):
        total = sum(sorted(rolls)[:num_keep]) + min_outcome
        mass = numpy.product([die.pmf()[roll] for die, roll in zip(dice, rolls)])
        counter.insert(total, mass)
    return counter.die()

@pytest.mark.parametrize('tuple_length', range(max_tuple_length + 1))
@pytest.mark.parametrize('num_values', range(1, max_num_values + 1))
def test_iter_sorted_tuples_length(tuple_length, num_values):
    counter = 0
    for _ in hdroller.die_sort.iter_sorted_tuples(tuple_length, num_values):
        counter += 1
    assert counter == hdroller.die_sort.num_sorted_tuples(tuple_length, num_values)

@pytest.mark.parametrize('tuple_length', range(1, max_tuple_length + 1))
@pytest.mark.parametrize('num_values', range(1, max_num_values + 1))
def test_iter_sorted_tuples_ordering(tuple_length, num_values):
    prev = (-1,)
    for curr in hdroller.die_sort.iter_sorted_tuples(tuple_length, num_values):
        assert curr > prev
        prev = curr
    
@pytest.mark.parametrize('tuple_length', range(max_tuple_length + 1))
@pytest.mark.parametrize('num_values', range(1, max_num_values + 1))
def test_iter_sorted_tuples_vs_ravel(tuple_length, num_values):
    for index, faces in enumerate(hdroller.die_sort.iter_sorted_tuples(tuple_length, num_values)):
        assert hdroller.die_sort.ravel_sorted_tuple(faces, num_values) == index

@pytest.mark.parametrize('num_dice', range(1, max_tuple_length + 1))
@pytest.mark.parametrize('num_keep', range(1, max_tuple_length + 1))
def test_keep_highest_vs_repeater(num_dice, num_keep):
    if num_keep > num_dice: return
    die = Die.d6
    dice = [die] * num_dice
    result = hdroller.die_sort.keep_highest(num_keep, *dice)
    expected = die.keep_highest(num_dice, num_keep)

    assert result.total_mass() == pytest.approx(1.0)
    assert result.ks_stat(expected) == pytest.approx(0.0)

@pytest.mark.parametrize('num_dice', range(1, max_tuple_length + 1))
@pytest.mark.parametrize('num_keep', range(1, max_tuple_length + 1))
def test_keep_lowest_vs_repeater(num_dice, num_keep):
    if num_keep > num_dice: return
    die = Die.d6
    dice = [die] * num_dice
    result = hdroller.die_sort.keep_lowest(num_keep, *dice)
    expected = die.keep_lowest(num_dice, num_keep)

    assert result.total_mass() == pytest.approx(1.0)
    assert result.ks_stat(expected) == pytest.approx(0.0)


@pytest.mark.parametrize('num_keep', range(4))
def test_keep_highest_mixed(num_keep):
    dice = [Die.d4.explode(1), Die.d6, Die.d6, Die.d8]
    result = hdroller.die_sort.keep_highest(num_keep, *dice)
    expected = bf_keep_highest(num_keep, *dice)
    
    assert result.total_mass() == pytest.approx(1.0)
    assert result.ks_stat(expected) == pytest.approx(0.0)

@pytest.mark.parametrize('num_keep', range(4))
def test_keep_lowest_mixed(num_keep):
    dice = [Die.d4.explode(1), Die.d6, Die.d6, Die.d8]
    result = hdroller.die_sort.keep_lowest(num_keep, *dice)
    expected = bf_keep_lowest(num_keep, *dice)
    
    assert result.total_mass() == pytest.approx(1.0)
    assert result.ks_stat(expected) == pytest.approx(0.0)