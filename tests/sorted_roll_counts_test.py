import icepool
import pytest


def test_all_slice():
    result = icepool.d6.pool(5)[:]
    assert result.sorted_roll_counts() == (1, 1, 1, 1, 1)


def test_two_highest_slice():
    pool = icepool.d6.pool(5)
    result = pool[3:5]
    assert result.sorted_roll_counts() == pool[3:].sorted_roll_counts()
    assert result.sorted_roll_counts() == pool[-2:].sorted_roll_counts()
    assert result.sorted_roll_counts() == pool[0, 0, 0, 1,
                                               1].sorted_roll_counts()
    assert result.sorted_roll_counts() == pool[..., 1, 1].sorted_roll_counts()


def test_two_highest_slice_short():
    pool = icepool.d6.pool(1)
    result = pool
    assert result.sorted_roll_counts() == pool[-2:].sorted_roll_counts()
    assert result.sorted_roll_counts() == pool[..., 1, 1].sorted_roll_counts()


def test_two_lowest_slice():
    pool = icepool.d6.pool(5)
    result = pool[0:2]
    assert result.sorted_roll_counts() == pool[:2].sorted_roll_counts()
    assert result.sorted_roll_counts() == pool[:-3].sorted_roll_counts()
    assert result.sorted_roll_counts() == pool[1, 1, 0, 0,
                                               0].sorted_roll_counts()
    assert result.sorted_roll_counts() == pool[1, 1, ...].sorted_roll_counts()


def test_two_lowest_slice_short():
    pool = icepool.d6.pool(1)
    result = pool
    assert result.sorted_roll_counts() == pool[:2].sorted_roll_counts()
    assert result.sorted_roll_counts() == pool[1, 1, ...].sorted_roll_counts()


def test_highest_minus_lowest_slice():
    pool = icepool.d6.pool(5)
    assert pool[-1, 0, 0, 0,
                1].sorted_roll_counts() == pool[-1, ...,
                                                1].sorted_roll_counts()


def test_highest_minus_lowest_slice_shorten():
    pool = icepool.d6.pool(1)
    assert pool[-1, ..., 1].sorted_roll_counts() == (0,)
