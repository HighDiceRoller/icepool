
import icepool
import pytest

def test_die():
    d = {}
    d[icepool.d6] = 100
    d[icepool.d12] = 200
    assert d[icepool.d6] == 100
    assert d[icepool.d12] == 200
    d[icepool.d6] = 300
    assert d[icepool.d6] == 300

def test_pool():
    d = {}
    d[icepool.Pool([icepool.d6, 5])] = 100
    assert d[icepool.Pool([icepool.d6, 5])] == 100

def test_die_construct():
    die = icepool.Die({icepool.d3 : 1, icepool.d3 + 3 : 1})
    assert die == icepool.d6
