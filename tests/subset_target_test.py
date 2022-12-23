from typing import Collection
import icepool
import pytest

from icepool import d, Die, Pool

from collections import Counter

targets_to_test = [
    (),
    (1,),
    (2,),
    (4,),
    (6,),
    (1, 6),
    (1, 3, 6),
    (1, 1, 1),
    (1, 1, 3, 6),
    (1, 1, 3, 3, 6, 6),
]


def test_contains_subset():
    assert Pool([1, 1, 2, 4, 4]).contains_subset([1, 2, 4]) == Die(True)
    assert Pool([1, 1, 2, 4, 4]).contains_subset([1, 2, 2, 4]) == Die(False)


def test_intersection_size():
    assert Pool([1, 1, 2, 4, 4]).intersection_size([1, 2, 4]) == Die(3)
    assert Pool([1, 1, 2, 4, 4]).intersection_size([1, 2, 2, 4]) == Die(3)


def test_largest_matching_set():
    result = Pool([1, 1, 2, 4, 4]).largest_matching_set().simplify()
    expected = Die(2)
    assert result == expected


def test_largest_matching_set_and_outcome() -> None:
    pool: Pool[int] = Pool([1, 1, 2, 4, 4])
    result = pool.largest_matching_set_and_outcome().simplify()
    expected = Die((2, 4))
    assert result == expected


def test_largest_straight_full():
    result = Pool([1, 2, 3]).largest_straight().simplify()
    expected = Die(3)
    assert result == expected


def test_largest_straight_gap():
    result = Pool([1, 2, 5, 10, 11]).largest_straight().simplify()
    expected = Die(2)
    assert result == expected


def test_largest_straight_include_outcome():
    result = Pool([1, 2, 3]).largest_straight_and_outcome().simplify()
    expected = Die((3, 3))
    assert result == expected


def test_largest_straight_include_outcome_tiebreaker():
    result = Pool([1, 2, 5, 10, 11]).largest_straight_and_outcome().simplify()
    expected = Die((2, 11))
    assert result == expected
