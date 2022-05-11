import _context

import icepool
import pytest

def test_invert():
    assert (~icepool.coin(1, 4)).mean() < 0

def test_and():
    assert (icepool.coin(1, 4) & icepool.coin(1, 4)).mean() == pytest.approx(1/16)
    
def test_or():
    assert (icepool.coin(1, 4) | icepool.coin(1, 4)).mean() == pytest.approx(7/16)

def test_xor():
    print(icepool.coin(1, 4) ^ icepool.coin(1, 4))
    print((icepool.coin(1, 4) ^ icepool.coin(1, 4)).probability(1))
    assert (icepool.coin(1, 4) ^ icepool.coin(1, 4)).mean() == pytest.approx(6/16)

def test_ifelse():
    result = icepool.coin(1, 2).if_else(icepool.d8, icepool.d6).reduce_weights()
    expected = icepool.Die(*range(1, 9), weights=[14, 14, 14, 14, 14, 14, 6, 6]).reduce_weights()
    assert result.equals(expected)