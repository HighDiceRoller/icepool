import _context

import hdroller
import pytest

def test_lt():
    assert (hdroller.d6 < hdroller.d6) == hdroller.bernoulli(15, 36)

def test_gt():
    assert (hdroller.d6 > hdroller.d6) == hdroller.bernoulli(15, 36)

def test_leq():
    assert (hdroller.d6 <= hdroller.d6) == hdroller.bernoulli(21, 36)

def test_geq():
    assert (hdroller.d6 >= hdroller.d6) == hdroller.bernoulli(21, 36)
    
def test_sign():
    assert (hdroller.d6 - 3).sign() == hdroller.die([2, 1, 3], min_outcome=-1)

def test_cmp():
    assert hdroller.d6.cmp(hdroller.d6 - 1) == hdroller.die([10, 5, 21], min_outcome=-1)