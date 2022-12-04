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

wilds_to_test = [
    (),
    (1,),
    (2,),
    (6,),
    (1, 6),
    (1, 3, 6),
]


@pytest.mark.parametrize('target', targets_to_test)
@pytest.mark.parametrize('wilds', wilds_to_test)
def test_contains_subset(target: Collection, wilds: Collection):
    result = d(6).pool(4).contains_subset(target, wilds=wilds)

    def expected_func(rolls):
        wild_rolls = [x for x in rolls if x in wilds]
        non_wild_rolls = [x for x in rolls if x not in wilds]
        non_wild_match = Counter(non_wild_rolls) & Counter(target)
        return non_wild_match.total() + len(wild_rolls) >= len(target)

    expected = d(6).pool(4).expand().map(expected_func)
    assert result == expected


@pytest.mark.parametrize('target', targets_to_test)
@pytest.mark.parametrize('wilds', wilds_to_test)
def test_intersection_size(target, wilds):
    result = d(6).pool(4).intersection_size(target, wilds=wilds)

    def expected_func(rolls):
        wild_rolls = [x for x in rolls if x in wilds]
        non_wild_rolls = [x for x in rolls if x not in wilds]
        non_wild_match = Counter(non_wild_rolls) & Counter(target)
        return min(non_wild_match.total() + len(wild_rolls), len(target))

    expected = d(6).pool(4).expand().map(expected_func)
    assert result == expected


@pytest.mark.parametrize('wilds', wilds_to_test)
def test_best_matching_set(wilds):
    result = d(6).pool(4).best_matching_set(wilds=wilds)

    def expected_func(rolls):
        wild_rolls = [x for x in rolls if x in wilds]
        non_wild_rolls = [x for x in rolls if x not in wilds]
        if non_wild_rolls:
            return max(Counter(non_wild_rolls).values()) + len(wild_rolls)
        else:
            return len(wild_rolls)

    expected = d(6).pool(4).expand().map(expected_func)
    assert result == expected


@pytest.mark.parametrize('wilds', wilds_to_test)
def test_best_matching_set_include_outcome(wilds):
    result = d(6).pool(4).best_matching_set(include_outcome=True, wilds=wilds)

    def expected_func(rolls):
        wild_rolls = [x for x in rolls if x in wilds]
        non_wild_rolls = [x for x in rolls if x not in wilds]
        if non_wild_rolls:
            count, mode = max(
                (v, k) for k, v in Counter(non_wild_rolls).items())
            return count + len(wild_rolls), mode
        else:
            return len(wild_rolls), 6

    expected = d(6).pool(4).expand().map(expected_func)
    assert result == expected


def test_best_straight_full():
    result = Pool([1, 2, 3]).best_straight().simplify()
    expected = Die(3)
    assert result == expected


def test_best_straight_gap():
    result = Pool([1, 2, 5, 10, 11]).best_straight().simplify()
    expected = Die(2)
    assert result == expected


def test_best_straight_include_outcome():
    result = Pool([1, 2, 3]).best_straight(include_outcome=True).simplify()
    expected = Die((3, 3))
    assert result == expected


def test_best_straight_include_outcome_tiebreaker():
    result = Pool([1, 2, 5, 10,
                   11]).best_straight(include_outcome=True).simplify()
    expected = Die((2, 11))
    assert result == expected
