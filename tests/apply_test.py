import _context

import icepool
import pytest

def test_apply_reroll():
    result = icepool.apply(lambda x: icepool.Reroll if x > 4 else x, icepool.d6)
    expected = icepool.d4
    assert result.equals(expected)

def test_apply_die():
    result = icepool.apply(lambda x: icepool.d6 + x, icepool.d6)
    expected = 2 @ icepool.d6
    assert result.equals(expected)
