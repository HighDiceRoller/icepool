import _context

import hdroller
import pytest

def test_d_syntax():
    assert hdroller.d6.weights() == (1,) * 6
    assert hdroller.d6.probability(0) == 0.0
    assert hdroller.d6.probability(1) == pytest.approx(1.0 / 6.0)
    assert hdroller.d6.probability(6) == pytest.approx(1.0 / 6.0)
    assert hdroller.d6.probability(7) == 0.0

def test_coin():
    b = hdroller.bernoulli(1, 2)
    c = hdroller.coin(1, 2)

    assert b.pmf() == pytest.approx([0.5, 0.5])
    assert c.pmf() == pytest.approx([0.5, 0.5])


