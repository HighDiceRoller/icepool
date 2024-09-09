import icepool
import numpy
import scipy.stats
import pytest

from icepool import d6, from_cumulative


def test_from_cumulative():
    outcomes = [1, 2, 3, 4, 5, 6]
    cumulative = [d6 <= x for x in outcomes]
    assert from_cumulative(outcomes, cumulative) == d6


def test_from_cumulative_reverse():
    outcomes = [1, 2, 3, 4, 5, 6]
    cumulative = [d6 >= x for x in outcomes]
    assert from_cumulative(outcomes, cumulative, reverse=True) == d6


def test_from_rv_norm():
    # Unfortunately pytest seems to hang on importing scipy.
    die = 100 @ icepool.d6
    norm_die = icepool.from_rv(scipy.stats.norm,
                               range(die.min_outcome(),
                                     die.max_outcome() + 1),
                               1000000,
                               loc=die.mean(),
                               scale=die.standard_deviation())
    assert die.probabilities('<=') == pytest.approx(
        norm_die.probabilities('<='), abs=1e-3)
