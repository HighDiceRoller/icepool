import _context

import icepool
import numpy
import scipy.stats
import pytest

def test_from_rv_norm():
    # Unfortunately pytest seems to hang on importing scipy.
    die = 100 @ icepool.d6
    norm_die = icepool.from_rv(scipy.stats.norm, range(die.min_outcome(), die.max_outcome()+1), 1000000, loc=die.mean(), scale=die.standard_deviation())
    die, norm_die = icepool.align(die, norm_die)
    print(die.ks_stat(norm_die))
    assert die.cdf() == pytest.approx(norm_die.cdf(), abs=1e-3)
