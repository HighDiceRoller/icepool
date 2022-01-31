import _context

import hdroller
import pytest

def test_ks_stat_standard_dice():
    assert hdroller.d10.ks_stat(hdroller.d20) == pytest.approx(0.5)

def test_ks_stat_flat_number():
    assert hdroller.die(10).ks_stat(hdroller.die(10)) == 0.0
    assert hdroller.die(10).ks_stat(hdroller.die(9)) == 1.0

def test_d6_median():
    assert hdroller.d6.median_left() == 3
    assert hdroller.d6.median_right() == 4
    assert hdroller.d6.median() == 3.5

def test_d7_median():
    assert hdroller.d7.median_left() == 4
    assert hdroller.d7.median_right() == 4
    assert hdroller.d7.median() == 4

def test_min_ppf():
    assert hdroller.d6.ppf_left(0) == 1
    assert hdroller.d6.ppf_right(0) == 1

def test_max_ppf():
    assert hdroller.d6.ppf_left(100) == 6
    assert hdroller.d6.ppf_right(100) == 6
