import _context

from hdroller import Die
import pytest

def test_d_syntax():
    assert Die.d6.weights() == pytest.approx([1.0] * 6)
    
def test_d_multiple():
    assert Die.d(1, 2, 2).weights() == pytest.approx([2, 3, 2, 1])

def test_coin():
    b = Die.bernoulli()
    c = Die.coin()

    assert b.pmf() == pytest.approx([0.5, 0.5])
    assert c.pmf() == pytest.approx([0.5, 0.5])


