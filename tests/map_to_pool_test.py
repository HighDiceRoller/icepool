import icepool
import pytest

from icepool import d6, Die, tupleize, map


def test_explode_to_pool():
    assert d6.explode_to_pool(3, depth=4).sum() == 3 @ d6.explode(depth=4)


def test_explode_to_pool_multi():
    assert d6.explode_to_pool(
        3, which=[5,
                  6], depth=4).sum() == 3 @ d6.explode(which=[5, 6], depth=4)


def test_map_to_pool():
    assert d6.pool(3).expand().map_to_pool().expand() == d6.pool(3).expand()


def test_reroll_to_pool_vs_reroll():
    assert d6.reroll_to_pool(3, [1], 3).sum() == 3 @ d6.reroll([1], depth=1)


def test_reroll_pool_vs_map():

    def expected_function(rolls):
        if rolls[2] < 4:
            return Die([
                tupleize(d6, rolls[1], rolls[2]),
                tupleize(rolls[0], d6, rolls[2]),
                tupleize(rolls[0], rolls[1], d6),
            ])
        elif rolls[1] < 4:
            return Die([
                tupleize(d6, rolls[1], rolls[2]),
                tupleize(rolls[0], d6, rolls[2]),
            ])
        elif rolls[0] < 4:
            return tupleize(d6, rolls[1], rolls[2])
        else:
            return rolls

    result = d6.reroll_to_pool(3, lambda x: x < 4, 1).expand()
    assert result.simplify() == map(
        expected_function,
        d6.pool(3)).map(lambda rolls: tuple(sorted(rolls))).simplify()
    assert result.denominator() == 6**4


def test_reroll_pool_empowered_spell():
    result = d6.reroll_to_pool(8, [1, 2, 3], 4, reroll_priority='lowest').sum()
    assert result.mean() == pytest.approx(33.61, abs=0.01)


def test_explode_empty():
    result = d6.explode_to_pool(3, [])
    assert result.sum().simplify() == 3 @ d6


def test_reroll_empty():
    result = d6.reroll_to_pool(3, [], 2)
    assert result.sum().simplify() == 3 @ d6

def test_reroll_drop():
    pool = (d6 - 3).reroll_to_pool(3, [0], 3, reroll_priority='drop')
    assert pool.keep_outcomes([0]).count().mean() == 0

def test_reroll_drop_sum():
    a = (d6 - 3).reroll_to_pool(3, [0], 3, reroll_priority='drop').sum()
    b = (d6 - 3).reroll_to_pool(3, [0], 3, reroll_priority='random').sum()
    assert a == b
