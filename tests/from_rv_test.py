import _context

import hdroller
#import numpy
#import scipy.stats
import pytest

def test_from_rv_norm():
    # Needs to be re-implemented.
    """
    die = hdroller.d(100, 6)
    norm_die = hdroller.from_rv(scipy.stats.norm, die.min_outcome(), die.max_outcome(), loc=die.mean(), scale=die.standard_deviation())
    die, norm_die = Die._align(die, norm_die)
    print(numpy.max(numpy.abs(norm_die.cdf() - die.cdf())))
    assert die.cdf() == pytest.approx(norm_die.cdf(), abs=1e-3)
    """
    pass
