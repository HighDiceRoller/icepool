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

def test_list_no_min_outcome():
    assert hdroller.die([2, 3, 3, 4, 4, 4, 5, 5, 6]) == 2 @ hdroller.d3

def test_trim():
    die = hdroller.die([0, 1, 1, 1, 1, 1, 1], min_outcome=0)
    assert not die.has_zero_weights()
    assert die == hdroller.d6

def test_trim_from_die():
    die = hdroller.die([0, 1, 1, 1, 1, 1, 1], min_outcome=0, trim=False)
    assert die.has_zero_weights()
    assert die != hdroller.d6
    assert hdroller.die(die) == hdroller.d6