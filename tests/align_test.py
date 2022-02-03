import _context

import hdroller
import pytest

def test_align_range_symmetric_difference():
    a, b = hdroller.align_range(hdroller.d4, hdroller.d6 + 1)
    assert a == hdroller.die([1, 1, 1, 1, 0, 0, 0], min_outcome=1, trim=False)
    assert b == hdroller.die([0, 1, 1, 1, 1, 1, 1], min_outcome=1, trim=False)

def test_align_range_subset():
    a, b = hdroller.align_range(hdroller.d4+1, hdroller.d8)
    assert a == hdroller.die([0, 1, 1, 1, 1, 0, 0, 0], min_outcome=1, trim=False)
    assert b == hdroller.die([1, 1, 1, 1, 1, 1, 1, 1], min_outcome=1, trim=False)

def test_trim():
    a, b = hdroller.align_range(hdroller.d4, hdroller.d6 + 1)
    assert a.trim() == hdroller.d4
    assert b.trim() == hdroller.d6 + 1
