import _context

from hdroller import Die
import numpy
import scipy.stats
import pytest

def test_from_rv_norm():
    die = Die.d(100, 6)
    norm_die = Die.from_rv(scipy.stats.norm, die.min_outcome(), die.max_outcome(), loc=die.mean(), scale=die.standard_deviation())
    die, norm_die = Die._align(die, norm_die)
    print(numpy.max(numpy.abs(norm_die.cdf() - die.cdf())))
    assert die.cdf() == pytest.approx(norm_die.cdf(), abs=1e-3)
