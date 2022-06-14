import _context

import icepool
import pytest

def test_all_slice():
    result = icepool.d6.pool(5)[:]
    assert result.count_sorted() == (1, 1, 1, 1, 1)

def test_two_highest_slice():
    pool = icepool.d6.pool(5)
    result = pool[3:5]
    assert result.count_sorted() == pool[3:].count_sorted()
    assert result.count_sorted() == pool[-2:].count_sorted()
    assert result.count_sorted() == pool[0,0,0,1,1].count_sorted()
    assert result.count_sorted() == pool[...,1,1].count_sorted()

def test_two_highest_lengthen():
    default_pool = icepool.d6.pool()
    pool = icepool.d6.pool(5)
    result = pool[3:5]
    assert result.count_sorted() == default_pool[3:5:5].count_sorted()
    assert result.count_sorted() == default_pool[-2::5].count_sorted()
    assert result.count_sorted() == default_pool[0,0,0,1,1].count_sorted()

def test_two_highest_slice_shorten():
    pool = icepool.d6.pool(1)
    result = pool
    assert result.count_sorted() == pool[-2:].count_sorted()
    assert result.count_sorted() == pool[...,1,1].count_sorted()

def test_two_lowest_slice():
    default_pool = icepool.d6.pool()
    pool = icepool.d6.pool(5)
    result = pool[0:2]
    assert result.count_sorted() == pool[:2].count_sorted()
    assert result.count_sorted() == pool[:-3].count_sorted()
    assert result.count_sorted() == pool[1,1,0,0,0].count_sorted()
    assert result.count_sorted() == pool[1,1,...].count_sorted()

def test_two_lowest_lengthen():
    default_pool = icepool.d6.pool()
    pool = icepool.d6.pool(5)
    result = pool[0:2]
    assert result.count_sorted() == default_pool[:2:5].count_sorted()
    assert result.count_sorted() == default_pool[:-3:5].count_sorted()
    assert result.count_sorted() == default_pool[1,1,0,0,0].count_sorted()

def test_two_lowest_slice_shorten():
    pool = icepool.d6.pool(1)
    result = pool
    assert result.count_sorted() == pool[:2].count_sorted()
    assert result.count_sorted() == pool[1,1,...].count_sorted()

def test_highest_minus_lowest_slice():
    pool = icepool.d6.pool(5)
    assert pool[-1,0,0,0,1].count_sorted() == pool[-1,...,1].count_sorted()

def test_highest_minus_lowest_slice_shorten():
    pool = icepool.d6.pool(1)
    assert pool[-1,...,1].count_sorted() == (0,)
