import _context

import hdroller
import pytest

def test_two_highest_slice():
    pool = hdroller.d6.pool(5)
    expected = pool[3:5]
    assert expected.count_dice() == pool[3:].count_dice()
    assert expected.count_dice() == pool[-2:].count_dice()
    assert expected.count_dice() == pool[0,0,0,1,1].count_dice()
    assert expected.count_dice() == pool[...,1,1].count_dice()

def test_two_highest_lengthen():
    empty_pool = hdroller.d6.pool()
    pool = hdroller.d6.pool(5)
    expected = pool[3:5]
    assert expected.count_dice() == empty_pool[3:5:5].count_dice()
    assert expected.count_dice() == empty_pool[-2::5].count_dice()
    assert expected.count_dice() == empty_pool[0,0,0,1,1].count_dice()

def test_two_highest_slice_shorten():
    pool = hdroller.d6.pool(1)
    expected = pool
    assert expected.count_dice() == pool[-2:].count_dice()
    assert expected.count_dice() == pool[...,1,1].count_dice()

def test_two_lowest_slice():
    empty_pool = hdroller.d6.pool()
    pool = hdroller.d6.pool(5)
    expected = pool[0:2]
    assert expected.count_dice() == pool[:2].count_dice()
    assert expected.count_dice() == pool[:-3].count_dice()
    assert expected.count_dice() == pool[1,1,0,0,0].count_dice()
    assert expected.count_dice() == pool[1,1,...].count_dice()

def test_two_lowest_lengthen():
    empty_pool = hdroller.d6.pool()
    pool = hdroller.d6.pool(5)
    expected = pool[0:2]
    assert expected.count_dice() == empty_pool[:2:5].count_dice()
    assert expected.count_dice() == empty_pool[:-3:5].count_dice()
    assert expected.count_dice() == empty_pool[1,1,0,0,0].count_dice()

def test_two_lowest_slice_shorten():
    pool = hdroller.d6.pool(1)
    expected = pool
    assert expected.count_dice() == pool[:2].count_dice()
    assert expected.count_dice() == pool[1,1,...].count_dice()

def test_highest_minus_lowest_slice():
    pool = hdroller.d6.pool(5)
    assert pool[-1,0,0,0,1].count_dice() == pool[-1,...,1].count_dice()

def test_highest_minus_lowest_slice_shorten():
    pool = hdroller.d6.pool(1)
    assert pool[-1,...,1].count_dice() == (0,)
