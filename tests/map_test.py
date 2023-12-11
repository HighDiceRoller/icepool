import icepool
import pytest

from icepool import d, d6, Die, coin
from fractions import Fraction

expected_d6x1 = icepool.Die(range(1, 13),
                            times=[6, 6, 6, 6, 6, 0, 1, 1, 1, 1, 1, 1]).trim()


def test_map_dict():
    die = icepool.d6.map({6: icepool.d6 + 6})
    assert die.probabilities() == pytest.approx(expected_d6x1.probabilities())


def test_map_func():
    die = icepool.d6.map(lambda x: icepool.d6 + 6 if x == 6 else 6 - x)
    assert die.probabilities() == pytest.approx(expected_d6x1.probabilities())


def test_map_mix():
    result = icepool.d6.map(lambda x: x if x >= 3 else icepool.Reroll)
    expected = icepool.d4 + 2
    assert result.equals(expected)


def test_map_depth():
    result = (icepool.d8 - 1).map(lambda x: x // 2, repeat=2).simplify()
    expected = icepool.d2 - 1
    assert result.equals(expected)


def test_map_star():
    a = icepool.Die([(0, 0)]).map(lambda x, y: (x, y), repeat=1)
    b = icepool.Die([(0, 0)]).map(lambda x, y: (x, y), repeat=2)
    c = icepool.Die([(0, 0)]).map(lambda x, y: (x, y), repeat=None)
    assert a == b
    assert b == c


def collatz(x: int) -> int:
    if x == 1:
        return 1
    elif x % 2:
        return x * 3 + 1
    else:
        return x // 2


def test_map_fixed_point():
    # Collatz conjecture.
    result = icepool.d100.map(collatz, repeat=None).simplify()
    expected = icepool.Die([1])
    assert result.equals(expected)


def test_map_fixed_point_1_cycle():

    def repl(outcome):
        if outcome >= 10:
            return outcome
        return outcome + icepool.Die([0, 1])

    result = icepool.Die([0]).map(repl, repeat=None).simplify()
    assert result.equals(icepool.Die([10]))


def test_map_and_time() -> None:
    # How many coin flips until two heads?
    initial: icepool.Die[int] = icepool.Die([0])
    result = initial.map_and_time(lambda x: x if x >= 2 else x + coin(1, 2),
                                  repeat=100)
    assert result.marginals[1].mean() == pytest.approx(4.0)


def test_random_walk():

    def repl(x):
        if abs(x) >= 2:
            return x
        return icepool.Die([x - 1, x + 1])

    result = icepool.Die([0]).map(repl, repeat=None).simplify()
    assert result.equals(icepool.Die([-2, 2]))


def test_random_walk_extra_arg():

    def repl(x, step):
        if abs(x) >= 2:
            return x
        else:
            return x + step

    result = icepool.map(repl, 0, Die([-1, 1]), repeat=None).simplify()
    result2 = Die([0]).map(repl, Die([-1, 1]), repeat=None).simplify()
    expected = Die([-2, 2])
    assert result == expected
    assert result2 == expected


def test_random_walk_biased():

    def repl(x):
        if abs(x) >= 2:
            return x
        return icepool.Die([x - 1, x + 1], times=[1, 2])

    result = icepool.Die([0]).map(repl, repeat=None).simplify()
    assert result.equals(icepool.Die([-2, 2], times=[1, 4]))


def test_random_walk_biased_extra_arg():

    def repl(x, step):
        if abs(x) >= 2:
            return x
        else:
            return x + step

    result = icepool.map(repl, 0, Die([-1, 1, 1]), repeat=None).simplify()
    result2 = Die([0]).map(repl, Die([-1, 1, 1]), repeat=None).simplify()
    expected = icepool.Die([-2, 2], times=[1, 4])
    assert result == expected
    assert result2 == expected


def test_is_in():
    result = (2 @ icepool.d6).is_in({2, 12})
    expected = icepool.coin(2, 36)
    assert result.equals(expected)


def test_count():
    result = icepool.d6.count(2, {2, 4})
    expected = 2 @ icepool.coin(2, 6)
    assert result.equals(expected)


def test_deck_map():
    result = icepool.Deck(range(13)).map(lambda x: x * 2).deal(2).sum()
    expected = icepool.Deck(range(13)).deal(2).sum() * 2
    assert result.equals(expected)


def test_deck_map_size_increase():
    # Not recommended, but technically well-formed.
    result = icepool.Deck(range(13)).map({12: icepool.Deck(range(12))})
    expected = icepool.Deck(range(12), times=2)
    assert result == expected


def test_mean_time_to_sum_d6():
    cdf = []
    for i in range(11):
        cdf.append(i @ d6 >= 10)
    expected = icepool.from_cumulative(range(11), cdf).mean()
    assert d6.mean_time_to_sum(10) == expected


def test_mean_time_to_sum_z6():
    cdf = []
    for i in range(11):
        cdf.append(i @ d(5) >= 10)
    expected = icepool.from_cumulative(range(11), cdf).mean() * Fraction(6, 5)
    assert (d6 - 1).mean_time_to_sum(10) == expected


def test_mean_time_to_sum_coin():
    assert icepool.coin(1, 2).mean_time_to_sum(10) == 20
