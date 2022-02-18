import _context

import hdroller
import pytest

def test_invert():
    assert (~hdroller.coin(1, 4)).mean() < 0

def test_and():
    assert (hdroller.coin(1, 4) & hdroller.coin(1, 4)).mean() == pytest.approx(1/16)
    
def test_or():
    assert (hdroller.coin(1, 4) | hdroller.coin(1, 4)).mean() == pytest.approx(7/16)

def test_xor():
    print(hdroller.coin(1, 4) ^ hdroller.coin(1, 4))
    print((hdroller.coin(1, 4) ^ hdroller.coin(1, 4)).probability(1))
    assert (hdroller.coin(1, 4) ^ hdroller.coin(1, 4)).mean() == pytest.approx(6/16)

def test_ifelse():
    result = hdroller.coin(1, 2).if_else(hdroller.d8, hdroller.d6).reduce()
    expected = hdroller.Die([14, 14, 14, 14, 14, 14, 6, 6], min_outcome=1).reduce()
    assert result.equals(expected)