import _context

import hdroller
import pytest

def test_dict():
    d = {}
    d[hdroller.Pool(hdroller.d6, 5)] = 100
    assert d[hdroller.Pool(hdroller.d6, 5)] == 100
