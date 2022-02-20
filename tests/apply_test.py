import _context

import hdroller
import pytest

def test_apply_reroll():
    result = hdroller.apply(lambda x: hdroller.Reroll if x > 4 else x, hdroller.d6)
    expected = hdroller.d4
    assert result.equals(expected)

def test_apply_die():
    result = hdroller.apply(lambda x: hdroller.d6 + x, hdroller.d6)
    expected = 2 @ hdroller.d6
    assert result.equals(expected)
