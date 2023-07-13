import icepool
import pytest

from icepool import d6, Die
from icepool.expression import multiset_function

# See https://rpg.stackexchange.com/q/171498/72732
# for approaches by myself and others.

expected = Die({
    0: 8848236,
    1: 73856630,
    2: 153052510,
    3: 257554860,
    4: 389406800,
    5: 550664770,
    6: 493136280,
    7: 196950375,
    8: 46377500,
    9: 6431250,
    10: 487500,
    11: 15625,
})


def final_score(outcome: int, count: int) -> int:
    if count == 0:
        return 0
    elif outcome < 6:
        return outcome
    else:
        return count + 5


def test_using_multiset_ops():
    mid_result = (d6.pool(6) - d6.pool(6)).highest_outcome_and_count()

    result = mid_result.map(final_score)
    assert result == expected


def test_using_multiset_function():

    @multiset_function
    def mid_result(a, b):
        return (a - b).highest_outcome_and_count()

    result = mid_result(d6.pool(6), d6.pool(6)).map(final_score)
    assert result == expected


def test_keep_outcomes():
    using_keep = (d6.pool(6).keep_outcomes(
        d6.pool(6))).highest_outcome_and_count()
    using_mul = (d6.pool(6) & (100 * d6.pool(6))).highest_outcome_and_count()
    assert using_keep == using_mul


def test_drop_outcomes():
    using_drop = (d6.pool(6).drop_outcomes(
        d6.pool(6))).highest_outcome_and_count()
    using_mul = (d6.pool(6) - (100 * d6.pool(6))).highest_outcome_and_count()
    assert using_drop == using_mul