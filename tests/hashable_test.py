import _context

import hdroller
import pytest

def test_dict():
    d = {}
    d[hdroller.pool(hdroller.d6, 5)] = 100
    assert d[hdroller.pool(hdroller.d6, 5)] == 100
