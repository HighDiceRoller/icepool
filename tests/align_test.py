
import icepool
import pytest

def test_align_range_symmetric_difference():
    a, b = icepool.align_range(icepool.d4, icepool.d6 + 1)
    assert a.equals(icepool.Die(range(1, 8), times=[1, 1, 1, 1, 0, 0, 0]))
    assert b.equals(icepool.Die(range(1, 8), times=[0, 1, 1, 1, 1, 1, 1]))

def test_align_range_subset():
    a, b = icepool.align_range(icepool.d4+1, icepool.d8)
    assert a.equals(icepool.Die(range(1, 9), times=[0, 1, 1, 1, 1, 0, 0, 0]))
    assert b.equals(icepool.Die(range(1, 9), times=[1, 1, 1, 1, 1, 1, 1, 1]))

def test_trim():
    a, b = icepool.align_range(icepool.d4, icepool.d6 + 1)
    assert a.trim().equals(icepool.d4)
    assert b.trim().equals(icepool.d6 + 1)

def test_die_set_range():
    result = icepool.d4.set_range(0, 6)
    assert result.outcomes() == (0, 1, 2, 3, 4, 5, 6)
