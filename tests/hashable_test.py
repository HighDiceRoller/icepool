import _context

import hdroller
import pytest

def test_dict():
    d = {}
    d[hdroller.d6] = 100
    assert d[hdroller.d6] == 100
