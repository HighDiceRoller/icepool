import icepool
import pytest


def test_pool_roll_eq():
    assert icepool.Pool([1, 2, 3, 4]) == icepool.Pool([1, 2, 3, 4])
    assert icepool.Pool([1, 2, 3, 4]) != icepool.Pool([1, 1, 2, 2, 3, 3, 4, 4])
    assert icepool.Pool([1, 2, 3, 4]) != icepool.d4.pool(1)


def test_pool_roll_sum():
    roll = icepool.Pool([1, 2, 3, 4])
    assert roll.sum() == icepool.Die([10])


def test_pool_roll_sum_duplicates():
    roll = icepool.Pool([1, 1, 1, 1, 2, 3, 4])
    assert roll.sum() == icepool.Die([13])


def test_pool_roll_dups():
    roll = icepool.Pool([1, 2, 3], times=[3, 2, 1])
    assert roll.sum() == icepool.Die([10])
