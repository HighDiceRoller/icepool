import _context

from hdroller import Die, PureDicePool
import numpy
import pytest

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
            pmf[total] += 1.0
        pmf /= numpy.power(self.single_len(), self._num_dice)
        return Die(pmf, min_outcome)

    def keep_index(self, index):
        pmf = numpy.zeros_like(self._single_die.pmf())
        min_outcome = self.single_min_outcome()
        for rolls in numpy.ndindex((self.single_len(),) * self._num_dice):
            picked = sorted(rolls)[index]
            pmf[picked] += 1.0
        pmf /= numpy.power(self.single_len(), self._num_dice)
        return Die(pmf, min_outcome)

def test_keep_highest_of_7d6():
    for num_keep in range(8):
        pool = PureDicePool(7, Die.d6)
        pool_result = pool.keep_highest(num_keep)

        brute_pool = PureDicePoolBruteForce(7, Die.d6)
        brute_pool_result = brute_pool.keep_highest(num_keep)
        
        print(pool_result)
        print(brute_pool_result)

        assert pool_result.ks_stat(brute_pool_result) == pytest.approx(0.0)

def test_keep_index_of_7d6():
    for index in range(7):
        pool = PureDicePool(7, Die.d6)
        pool_result = pool.keep_index(index)

        brute_pool = PureDicePoolBruteForce(7, Die.d6)
        brute_pool_result = brute_pool.keep_index(index)

        assert pool_result.ks_stat(brute_pool_result) == pytest.approx(0.0)
        
