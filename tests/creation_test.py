import _context

from hdroller import Die
import pytest

def test_d_syntax():
    assert Die.d6.ks_stat(Die([1/6] * 6, 1)) == pytest.approx(0.0)

def test_coin():
    b = Die.bernoulli()
    c = Die.coin()

    assert b.pmf() == pytest.approx([0.5, 0.5])
    assert c.pmf() == pytest.approx([0.5, 0.5])


