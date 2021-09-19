import _context

from hdroller import Die
import pytest

"""
Tests Die.mix() and its derivatives.
"""

def test_mix_d6_faces():
    assert Die.mix(1, 2, 3, 4, 5, 6).pmf() == pytest.approx(Die.d6.pmf())
    assert Die.mix([1, 2, 3, 4, 5, 6]).pmf() == pytest.approx(Die.d6.pmf())

def test_mix_identical():
    assert Die.mix(Die.d6, Die.d6, Die.d6, Die.d6).pmf() == pytest.approx(Die.d6.pmf())

def test_mix_weight():
    outcomes = range(2, 13)
    mix_weights = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
    assert Die.mix(*outcomes, mix_weights=mix_weights).pmf() == pytest.approx(Die.d(2, 6).pmf())
    
def test_mix_mixed():
    die = Die.mix(Die.d4, Die.d6)
    assert die.pmf() == pytest.approx([5/24] * 4 + [2/24] * 2)

expected_d6x1 = Die([1/6] * 5 + [0] + [1/36] * 6, 1)

def test_relabel_array():
    die = Die.d6.relabel([5, 4, 1, 2, 3, Die.d6 + 6])
    assert die.pmf() == pytest.approx(expected_d6x1.pmf())

def test_relabel_dict():
    die = Die.d6.relabel({6 : Die.d6+6})
    assert die.pmf() == pytest.approx(expected_d6x1.pmf())

def test_relabel_func():
    die = Die.d6.relabel(lambda x: Die.d6 + 6 if x == 6 else 6 - x)
    assert die.pmf() == pytest.approx(expected_d6x1.pmf())