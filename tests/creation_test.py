import _context

import hdroller
import pytest

def test_d_syntax():
    assert hdroller.d6.weights() == pytest.approx([1.0] * 6)
    assert hdroller.d6.probability(0) == 0.0
    assert hdroller.d6.probability(1) == pytest.approx(1.0 / 6.0)
    assert hdroller.d6.probability(6) == pytest.approx(1.0 / 6.0)
    assert hdroller.d6.probability(7) == 0.0
    
def test_d_multiple():
    assert hdroller.d(1, 2, 2) == hdroller.die([2, 3, 2, 1], 1)

def test_coin():
    b = Die.bernoulli()
    c = Die.coin()

    assert b.pmf() == pytest.approx([0.5, 0.5])
    assert c.pmf() == pytest.approx([0.5, 0.5])


