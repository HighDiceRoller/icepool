import _context

from hdroller import Die
import numpy
import scipy.stats
import pytest

def test_from_rv_norm():
    die = Die.d(1000, 6)
    norm_die = Die.from_rv(scipy.stats.norm, die.min_outcome(), die.max_outcome(), loc=die.mean(), scale=die.standard_deviation())
    print(numpy.max(numpy.abs(norm_die.cdf() - die.cdf())))
    assert die.cdf() == pytest.approx(norm_die.cdf(), abs=1e-4)
