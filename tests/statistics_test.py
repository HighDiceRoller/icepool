import icepool
import pytest

from icepool import Die
from fractions import Fraction


def test_d6_mean():
    assert icepool.d6.mean() == 3.5


def test_d8_variance():
    assert icepool.d8.variance() == 63 / 12


def test_kolmogorov_smirnov_standard_dice():
    assert icepool.d10.kolmogorov_smirnov(icepool.d20) == Fraction(1, 2)


def test_kolmogorov_smirnov_flat_number():
    assert icepool.Die([10]).kolmogorov_smirnov(icepool.Die([10])) == 0
    assert icepool.Die([10]).kolmogorov_smirnov(icepool.Die([9])) == 1


def test_d6_median():
    assert icepool.d6.median_low() == 3
    assert icepool.d6.median_high() == 4
    assert icepool.d6.median() == 3.5


def test_d7_median():
    assert icepool.d7.median_low() == 4
    assert icepool.d7.median_high() == 4
    assert icepool.d7.median() == 4


def test_min_quantile():
    assert icepool.d6.quantile_low(0) == 1
    assert icepool.d6.quantile_high(0) == 1


def test_max_quantile():
    assert icepool.d6.quantile_low(100) == 6
    assert icepool.d6.quantile_high(100) == 6


def test_entropy_with_zeros():
    assert Die({1: 1, 2: 0, 3: 1}).entropy() == 1.0
