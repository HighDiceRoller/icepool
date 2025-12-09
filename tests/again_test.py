import icepool
import pytest

from icepool import Again, d, d6, Die, Reroll, Restart

import math


def test_again_evaluate():
    x = Again
    assert x._evaluate(d6) == d6


def test_again_evaluate_plus_6():
    x = Again + 6
    assert x._evaluate(d6) == d6 + 6


def test_again_evaluate_plus_d6():
    x = Again + d6
    assert x._evaluate(d6) == 2 @ d6


def test_again_evaluate_d6_plus():
    x = d6 + Again
    assert x._evaluate(d6) == 2 @ d6


def test_again_evaluate_plus_again():
    x = Again + Again
    assert x._evaluate(d6) == 2 @ d6


def test_explode_d6_depth_0():
    die = Die([1, 2, 3, 4, 5, 6 + Again], again_depth=0)
    assert die == d6


def test_explode_d6_depth_1():
    die = Die([1, 2, 3, 4, 5, 6 + Again], again_depth=1)
    assert die == Die({
        1: 6,
        2: 6,
        3: 6,
        4: 6,
        5: 6,
        7: 1,
        8: 1,
        9: 1,
        10: 1,
        11: 1,
        12: 1,
    })


def test_again_plus_again_depth_0():
    die = Die([1, 2, 3, 4, 5, Again + Again], again_depth=0, again_end=3)
    assert die == Die([1, 2, 3, 4, 5, 6])


def test_again_plus_again_depth_1():
    die = Die([1, 2, 3, 4, 5, Again + Again], again_end=3)
    assert die == Die([1, 2, 3, 4, 5, 2 @ d6])


def test_again_reroll_depth_0():
    die = Die([1, 2, 3, 4, 5, 6 + Again], again_depth=0, again_end=Reroll)
    assert die == d(5)


def test_again_reroll_depth_1():
    die = Die([1, 2, 3, 4, 5, 6 + Again], again_depth=1, again_end=Reroll)
    assert die == d6.map({6: 6 + d(5)})


def test_again_infinity():
    die = Die([1, 2, 3, 4, 5, Again], again_depth=0, again_end=math.inf)
    assert die == Die([1, 2, 3, 4, 5, math.inf])


def test_owod():
    result = Die({0: 7, 1: 2, Again + 1: 1}, again_depth=3)
    sub_expected = Die({-1: 7, 0: 2, 1: 1})
    expected = sub_expected
    expected = expected.map({1: 1 + sub_expected})
    expected = expected.map({2: 2 + sub_expected})
    expected = expected.map({3: 3 + icepool.lowest(sub_expected, 0)})
    expected = expected + 1
    assert result == expected


def test_is_additive():
    assert Again.is_additive
    assert (Again + Again).is_additive
    assert (2 @ Again).is_additive
    assert not (2 * Again).is_additive
    assert (d6 @ Again).is_additive
    assert not ((d6 - 2) @ Again).is_additive


@pytest.mark.parametrize('n', [0, 1, 2])
def test_again_count(n):
    count = Die([1, 2, 3, 4, 5, 6 + Again], again_count=n)
    depth = d6.explode(depth=n)
    assert count == depth


def test_again_count_double_restart():
    result = Die([1, 2, 3, 4, 5, 6 + Again + Again],
                 again_count=1,
                 again_end=icepool.Restart)
    expected = d(5)
    assert result.simplify() == expected


def test_again_count_double_reroll():
    result = Die([1, 2, 3, 4, 5, 6 + Again + Again],
                 again_count=0,
                 again_end=icepool.Reroll)
    expected = d6.map({6: 6 + 2 @ d(5)})
    assert result == expected
