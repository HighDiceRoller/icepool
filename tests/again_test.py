import icepool
import pytest

from icepool import Again, d6, Die, Reroll


def test_again_evaluate():
    x = Again()
    assert x.evaluate(d6) == d6


def test_again_evaluate_plus_6():
    x = Again() + 6
    assert x.evaluate(d6) == d6 + 6


def test_again_evaluate_plus_again():
    x = Again() + Again()
    assert x.evaluate(d6) == 2 @ d6


def test_explode_d6_depth_0():
    die = Die([1, 2, 3, 4, 5, 6 + Again()], max_depth=0)
    assert die == d6


def test_explode_d6_depth_1():
    die = Die([1, 2, 3, 4, 5, 6 + Again()], max_depth=1)
    assert die == d6.explode(max_depth=1)


def test_explode_d6_depth_4():
    die = Die([1, 2, 3, 4, 5, 6 + Again()], max_depth=4)
    assert die == d6.explode(max_depth=4)


def test_again_plus_again_depth_0():
    die = Die([1, 2, 3, 4, 5, Again() + Again()], max_depth=0, again_end=3)
    assert die == Die([1, 2, 3, 4, 5, 6])


def test_again_plus_again_depth_1():
    die = Die([1, 2, 3, 4, 5, Again() + Again()], again_end=3)
    assert die == Die([1, 2, 3, 4, 5, 2 @ d6])


def test_again_reroll():
    die = Die([1, 2, 3, 4, 5, Again()], max_depth=0, again_end=Reroll)
    assert die == icepool.d(5)
