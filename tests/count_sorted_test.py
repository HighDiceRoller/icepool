import _context

import icepool
import pytest

def test_all_slice():
    result = icepool.d6.pool(5)[:]
    assert result.post_roll_counts() == (1, 1, 1, 1, 1)

def test_two_highest_slice():
    pool = icepool.d6.pool(5)
    result = pool[3:5]
    assert result.post_roll_counts() == pool[3:].post_roll_counts()
    assert result.post_roll_counts() == pool[-2:].post_roll_counts()
    assert result.post_roll_counts() == pool[0,0,0,1,1].post_roll_counts()
    assert result.post_roll_counts() == pool[...,1,1].post_roll_counts()

def test_two_highest_lengthen():
    default_pool = icepool.d6.pool()
    pool = icepool.d6.pool(5)
    result = pool[3:5]
    assert result.post_roll_counts() == default_pool[3:5:5].post_roll_counts()
    assert result.post_roll_counts() == default_pool[-2::5].post_roll_counts()
    assert result.post_roll_counts() == default_pool[0,0,0,1,1].post_roll_counts()

def test_two_highest_slice_shorten():
    pool = icepool.d6.pool(1)
    result = pool
    assert result.post_roll_counts() == pool[-2:].post_roll_counts()
    assert result.post_roll_counts() == pool[...,1,1].post_roll_counts()

def test_two_lowest_slice():
    default_pool = icepool.d6.pool()
    pool = icepool.d6.pool(5)
    result = pool[0:2]
    assert result.post_roll_counts() == pool[:2].post_roll_counts()
    assert result.post_roll_counts() == pool[:-3].post_roll_counts()
    assert result.post_roll_counts() == pool[1,1,0,0,0].post_roll_counts()
    assert result.post_roll_counts() == pool[1,1,...].post_roll_counts()

def test_two_lowest_lengthen():
    default_pool = icepool.d6.pool()
    pool = icepool.d6.pool(5)
    result = pool[0:2]
    assert result.post_roll_counts() == default_pool[:2:5].post_roll_counts()
    assert result.post_roll_counts() == default_pool[:-3:5].post_roll_counts()
    assert result.post_roll_counts() == default_pool[1,1,0,0,0].post_roll_counts()

def test_two_lowest_slice_shorten():
    pool = icepool.d6.pool(1)
    result = pool
    assert result.post_roll_counts() == pool[:2].post_roll_counts()
    assert result.post_roll_counts() == pool[1,1,...].post_roll_counts()

def test_highest_minus_lowest_slice():
    pool = icepool.d6.pool(5)
    assert pool[-1,0,0,0,1].post_roll_counts() == pool[-1,...,1].post_roll_counts()

def test_highest_minus_lowest_slice_shorten():
    pool = icepool.d6.pool(1)
    assert pool[-1,...,1].post_roll_counts() == (0,)
