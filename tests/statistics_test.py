import _context

import icepool
import pytest

def test_d6_mean():
    assert icepool.d6.mean() == 3.5
    
def test_d8_variance():
    assert icepool.d8.variance() == 63 / 12

def test_kolmogorov_smirnov_standard_dice():
    assert icepool.d10.kolmogorov_smirnov(icepool.d20) == pytest.approx(0.5)

def test_kolmogorov_smirnov_flat_number():
    assert icepool.Die([10]).kolmogorov_smirnov(icepool.Die([10])) == 0.0
    assert icepool.Die([10]).kolmogorov_smirnov(icepool.Die([9])) == 1.0

def test_d6_median():
    assert icepool.d6.median_left() == 3
    assert icepool.d6.median_right() == 4
    assert icepool.d6.median() == 3.5

def test_d7_median():
    assert icepool.d7.median_left() == 4
    assert icepool.d7.median_right() == 4
    assert icepool.d7.median() == 4

def test_min_quantile():
    assert icepool.d6.quantile_left(0) == 1
    assert icepool.d6.quantile_right(0) == 1

def test_max_quantile():
    assert icepool.d6.quantile_left(100) == 6
    assert icepool.d6.quantile_right(100) == 6
