import _context

from hdroller import Die
import pytest

def test_d_syntax():
    assert Die.d6.ks_stat(Die([1/6] * 6, 1)) == pytest.approx(0.0)

def test_mix_d6_faces():
    assert Die.mix(1, 2, 3, 4, 5, 6).pmf() == pytest.approx(Die.d6.pmf())

def test_mix_identical():
    assert Die.mix(Die.d6, Die.d6, Die.d6, Die.d6).pmf() == pytest.approx(Die.d6.pmf())

def test_mix_weight():
    outcomes = range(2, 13)
    weights = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
    assert Die.mix(*outcomes, weights=weights).pmf() == pytest.approx(Die.d(2, 6).pmf())
