import _context

from hdroller import Die
import pytest

def test_explode_basic():
    result = Die.d10.explode(2)
    expected = Die([0.1]*9  + [0] +
                   [0.01]*9 + [0] +
                   [0.001]*10, 1)
    assert result.ks_stat(expected) == pytest.approx(0.0)

def test_explode_chance():
    result = Die(Die.d10 >= 9).explode(3, chance=0.1)
    print(result)
    expected = Die([1.0 - 0.2,
                    0.2 - 0.02,
                    0.02 - 0.002,
                    0.002 - 0.0002,
                    0.0002], 0)
    assert result.ks_stat(expected) == pytest.approx(0.0)


