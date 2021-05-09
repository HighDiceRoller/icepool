import _context

from hdroller import Die, PureDicePool
import numpy
import pytest

abs_tol = 1e-9

class PureDicePoolBruteForce():
    def __init__(self, num_dice, single_die):
        self._num_dice = num_dice
        self._single_die = single_die

    def single_len(self):
        return len(self._single_die)
        
    def single_min_outcome(self):
        return self._single_die.min_outcome()

    def keep_highest(self, num_keep):
        if num_keep == 0: return Die(0)
        pmf_length = (self.single_len() - 1) * num_keep + 1
        min_outcome = self.single_min_outcome() * num_keep
        pmf = numpy.zeros((pmf_length,))
        for rolls in numpy.ndindex((self.single_len(),) * self._num_dice):
            total = sum(sorted(rolls)[-num_keep:])
            mass = numpy.product(self._single_die.pmf()[numpy.array(rolls)])
            pmf[total] += mass
        return Die(pmf, min_outcome)

    def keep_index(self, index):
        pmf = numpy.zeros_like(self._single_die.pmf())
        min_outcome = self.single_min_outcome()
        for rolls in numpy.ndindex((self.single_len(),) * self._num_dice):
            picked = sorted(rolls)[index]
            mass = numpy.product(self._single_die.pmf()[numpy.array(rolls)])
            pmf[picked] += mass
        return Die(pmf, min_outcome)

@pytest.mark.parametrize('num_keep', range(8))
def test_keep_highest_of_7d6(num_keep):
    num_dice = 7
    single_die = Die.d6

    pool = PureDicePool(num_dice, single_die)
    pool_result = pool.keep_highest(num_keep)

    brute_pool = PureDicePoolBruteForce(num_dice, single_die)
    brute_pool_result = brute_pool.keep_highest(num_keep)

    assert pool_result.ks_stat(brute_pool_result) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('num_keep', range(9))
def test_keep_highest_of_8_weighted(num_keep):
    num_dice = 8
    single_die = Die.from_faces([1, 1, 1, 2, 2, 2, 2, 3])

    pool = PureDicePool(num_dice, single_die)
    pool_result = pool.keep_highest(num_keep)

    brute_pool = PureDicePoolBruteForce(num_dice, single_die)
    brute_pool_result = brute_pool.keep_highest(num_keep)

    assert pool_result.ks_stat(brute_pool_result) == pytest.approx(0.0, abs=abs_tol)

@pytest.mark.parametrize('index', range(7))
def test_keep_index_of_7d6(index):
    num_dice = 7
    single_die = Die.d6
    
    pool = PureDicePool(num_dice, single_die)
    pool_result = pool.keep_index(index)

    brute_pool = PureDicePoolBruteForce(num_dice, single_die)
    brute_pool_result = brute_pool.keep_index(index)

    assert pool_result.ks_stat(brute_pool_result) == pytest.approx(0.0, abs=abs_tol)
        
