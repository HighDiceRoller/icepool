import _context

from hdroller import Die
import pytest

def test_invert():
    assert (~Die(0.25) == 1) == pytest.approx(0.75)

def test_and():
    assert Die(0.25) & Die(0.25) == pytest.approx(1/16)
    
def test_or():
    assert Die(0.25) | Die(0.25) == pytest.approx(7/16)

def test_xor():
    assert Die(0.25) ^ Die(0.25) == pytest.approx(6/16)
