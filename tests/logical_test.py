import _context

import hdroller
import pytest

def test_invert():
    assert float(~Die.coin(0.25)) == pytest.approx(0.75)

def test_and():
    assert float(Die.coin(0.25) & Die.coin(0.25)) == pytest.approx(1/16)
    
def test_or():
    assert float(Die.coin(0.25) | Die.coin(0.25)) == pytest.approx(7/16)

def test_xor():
    print(Die.coin(0.25) ^ Die.coin(0.25))
    print((Die.coin(0.25) ^ Die.coin(0.25)).probability(1))
    assert float(Die.coin(0.25) ^ Die.coin(0.25)) == pytest.approx(6/16)
