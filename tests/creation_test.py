import _context

from hdroller import Die
import pytest

def test_d_syntax():
    assert Die.d6.ks_stat(Die([1/6] * 6, 1)) == pytest.approx(0.0)

