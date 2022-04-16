import _context

import icepool
import pytest

def test_dict():
    d = {}
    d[icepool.Pool(icepool.d6, 5)] = 100
    assert d[icepool.Pool(icepool.d6, 5)] == 100
