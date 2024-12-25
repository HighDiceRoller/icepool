from typing import Collection
import icepool
import pytest

from icepool import d, Die, Order, Pool
from icepool.multiset_expression import MultisetExpression

targets_to_test = [
    (),
    (1, ),
    (2, ),
    (4, ),
    (6, ),
    (1, 6),
    (1, 3, 6),
    (1, 1, 1),
    (1, 1, 3, 6),
    (1, 1, 3, 3, 6, 6),
]


def test_contains_subset():
    assert Pool([1, 1, 2, 4, 4]).issuperset([1, 2, 4]) == Die([True])
    assert Pool([1, 1, 2, 4, 4]).issuperset([1, 2, 2, 4]) == Die([False])


def test_intersection_size():
    assert (Pool([1, 1, 2, 4, 4]) & [1, 2, 4]).count() == Die([3])
    assert (Pool([1, 1, 2, 4, 4]) & [1, 2, 2, 4]).count() == Die([3])


def test_keep_outcomes_size():
    assert Pool([1, 1, 2, 4, 4]).keep_outcomes([1, 2]).count() == Die([3])


def test_drop_outcomes_size():
    assert Pool([1, 1, 2, 4, 4]).drop_outcomes([1, 2]).count() == Die([2])


def test_largest_matching_set():
    result = Pool([1, 1, 2, 4, 4]).largest_count().simplify()
    expected = Die([2])
    assert result == expected


def test_largest_matching_set_and_outcome() -> None:
    pool: Pool[int] = Pool([1, 1, 2, 4, 4])
    result = pool.largest_count_and_outcome().simplify()
    expected = Die([(2, 4)])
    assert result == expected


def test_all_matching_sets() -> None:
    pool: Pool[int] = Pool([1, 1, 2, 4, 4])
    result = pool.all_counts().simplify()
    expected = Die([(2, 2, 1)])
    assert result == expected


def test_largest_straight_full():
    result = Pool([1, 2, 3]).largest_straight().simplify()
    expected = Die([3])
    assert result == expected


def test_largest_straight_gap():
    result = Pool([1, 2, 5, 10, 11]).largest_straight().simplify()
    expected = Die([2])
    assert result == expected


def test_largest_straight_include_outcome():
    result = Pool([1, 2, 3]).largest_straight_and_outcome().simplify()
    expected = Die([(3, 3)])
    assert result == expected


def test_largest_straight_include_outcome_tiebreaker():
    result = Pool([1, 2, 5, 10, 11]).largest_straight_and_outcome().simplify()
    expected = Die([(2, 11)])
    assert result == expected


def test_all_straights():
    result = Pool([1, 1, 2, 3, 3, 5]).all_straights().simplify()
    expected = Die([(3, 1, 1, 1)])
    assert result == expected


def test_all_straights_reduce_counts():
    # cribbage double-double run and an extra
    result = Pool([1, 1, 2, 3, 3, 5]).all_straights_reduce_counts().simplify()
    expected = Die([((3, 4), (1, 1))])
    assert result == expected


def test_argsort():
    result = MultisetExpression.argsort([10, 9, 5], [9, 9])
    expected = Die([((0, ), (0, 1, 1), (0, ))])
    assert result == expected


def test_count_subsets():
    result = (d(6).pool(6) // [1, 2, 3]) > 0
    expected = d(6).pool(6) >= [1, 2, 3]
    assert result == expected

    result = (d(6).pool(6) // [1, 2, 3]) > 1
    expected = d(6).pool(6) >= [1, 2, 3] * 2
    assert result == expected
