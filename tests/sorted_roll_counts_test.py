import icepool
import pytest


def test_all_slice():
    result = icepool.d6.pool(5)[:]
    assert result.keep_tuple() == (1, 1, 1, 1, 1)


def test_two_highest_slice():
    pool = icepool.d6.pool(5)
    result = pool[3:5]
    assert result.keep_tuple() == pool[3:].keep_tuple()
    assert result.keep_tuple() == pool[-2:].keep_tuple()
    assert result.keep_tuple() == pool[0, 0, 0, 1, 1].keep_tuple()
    assert result.keep_tuple() == pool[..., 1, 1].keep_tuple()


def test_two_highest_slice_short():
    pool = icepool.d6.pool(1)
    result = pool
    assert result.keep_tuple() == pool[-2:].keep_tuple()
    assert result.keep_tuple() == pool[..., 1, 1].keep_tuple()


def test_two_lowest_slice():
    pool = icepool.d6.pool(5)
    result = pool[0:2]
    assert result.keep_tuple() == pool[:2].keep_tuple()
    assert result.keep_tuple() == pool[:-3].keep_tuple()
    assert result.keep_tuple() == pool[1, 1, 0, 0, 0].keep_tuple()
    assert result.keep_tuple() == pool[1, 1, ...].keep_tuple()


def test_two_lowest_slice_short():
    pool = icepool.d6.pool(1)
    result = pool
    assert result.keep_tuple() == pool[:2].keep_tuple()
    assert result.keep_tuple() == pool[1, 1, ...].keep_tuple()


def test_highest_minus_lowest_slice():
    pool = icepool.d6.pool(5)
    assert pool[-1, 0, 0, 0, 1].keep_tuple() == pool[-1, ..., 1].keep_tuple()


def test_highest_minus_lowest_slice_shorten():
    pool = icepool.d6.pool(1)
    assert pool[-1, ..., 1].keep_tuple() == (0, )
