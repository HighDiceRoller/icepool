import _context

from hdroller import Die
import numpy
import pytest

abs_tol = 1e-9

class BruteForceDieRepeater():
    def __init__(self, die):
        self._die = die

    def keep_highest(self, num_dice, num_keep):
        if num_keep == 0: return Die(0)
        pmf_length = (len(self._die) - 1) * num_keep + 1
        min_outcome = self._die.min_outcome() * num_keep
        pmf = numpy.zeros((pmf_length,))
        for rolls in numpy.ndindex((len(self._die),) * num_dice):
            total = sum(sorted(rolls)[-num_keep:])
            mass = numpy.product(self._die.pmf()[numpy.array(rolls)])
            pmf[total] += mass
        return Die(pmf, min_outcome)
        
    def keep_lowest(self, num_dice, num_keep):
        if num_keep == 0: return Die(0)
        pmf_length = (len(self._die) - 1) * num_keep + 1
        min_outcome = self._die.min_outcome() * num_keep
        pmf = numpy.zeros((pmf_length,))
        for rolls in numpy.ndindex((len(self._die),) * num_dice):
            total = sum(sorted(rolls)[:num_keep])
            mass = numpy.product(self._die.pmf()[numpy.array(rolls)])
            pmf[total] += mass
        return Die(pmf, min_outcome)

    def keep_index(self, num_dice, index):
        pmf = numpy.zeros_like(self._die.pmf())
        min_outcome = self._die.min_outcome()
        for rolls in numpy.ndindex((len(self._die),) * num_dice):
            picked = sorted(rolls)[index]
            mass = numpy.product(self._die.pmf()[numpy.array(rolls)])
            pmf[picked] += mass
        return Die(pmf, min_outcome)

@pytest.mark.parametrize('num_keep', range(6))
def test_keep_highest_of_5d6(num_keep):
    num_dice = 5
    die = Die.d6

    result = die.keep_highest(num_dice, num_keep)
    print(result)
    brute_result = BruteForceDieRepeater(die).keep_highest(num_dice, num_keep)

    assert result.ks_stat(brute_result) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('num_keep', range(6))
def test_keep_lowest_of_5d6(num_keep):
    num_dice = 5
    die = Die.d6

    result = die.keep_lowest(num_dice, num_keep)
    print(result)
    brute_result = BruteForceDieRepeater(die).keep_lowest(num_dice, num_keep)

    assert result.ks_stat(brute_result) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('num_keep', range(9))
def test_keep_highest_of_8_weighted(num_keep):
    num_dice = 8
    die = Die.from_faces([1, 1, 1, 2, 2, 2, 2, 3])

    result = die.keep_highest(num_dice, num_keep)
    brute_result = BruteForceDieRepeater(die).keep_highest(num_dice, num_keep)

    assert result.ks_stat(brute_result) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('index', range(5))
def test_keep_index_of_5d6(index):
    num_dice = 5
    die = Die.d6
    
    result = die.keep_index(num_dice, index)
    brute_result = BruteForceDieRepeater(die).keep_index(num_dice, index)

    assert result.ks_stat(brute_result) == pytest.approx(0.0, abs=abs_tol)
