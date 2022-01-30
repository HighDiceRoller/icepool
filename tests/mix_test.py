import _context

import hdroller
import pytest

"""
Tests Die.mix() and its derivatives.
"""

def test_mix_d6_faces():
    assert Die.mix(1, 2, 3, 4, 5, 6) == hdroller.d6
    assert Die.mix([1, 2, 3, 4, 5, 6]) == hdroller.d6

def test_mix_identical():
    assert Die.mix(hdroller.d6, hdroller.d6, hdroller.d6, hdroller.d6).pmf() == pytest.approx(hdroller.d6.pmf())

def test_mix_weight():
    outcomes = range(2, 13)
    mix_weights = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
    assert Die.mix(*outcomes, mix_weights=mix_weights) == hdroller.d(2, 6)
    
def test_mix_mixed():
    die = Die.mix(hdroller.d4, hdroller.d6)
    assert die == hdroller.die([5, 5, 5, 5, 2, 2], 1)

expected_d6x1 = hdroller.die([6, 6, 6, 6, 6, 0, 1, 1, 1, 1, 1, 1], 1)

def test_relabel_array():
    die = hdroller.d6.relabel([5, 4, 1, 2, 3, hdroller.d6 + 6])
    assert die.pmf() == pytest.approx(expected_d6x1.pmf())

def test_relabel_dict():
    die = hdroller.d6.relabel({6 : hdroller.d6+6})
    assert die.pmf() == pytest.approx(expected_d6x1.pmf())

def test_relabel_func():
    die = hdroller.d6.relabel(lambda x: hdroller.d6 + 6 if x == 6 else 6 - x)
    assert die.pmf() == pytest.approx(expected_d6x1.pmf())