import icepool
import pytest

from icepool import d, d6, d10, Die, coin, map, tupleize
from fractions import Fraction

expected_d6x1 = icepool.Die([1, 2, 3, 4, 5] * 6 + [7, 8, 9, 10, 11, 12])


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
    c = icepool.Die([(0, 0)]).map(lambda x, y: (x, y), repeat='inf')
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
    result = icepool.d100.map(collatz, repeat='inf').simplify()
    expected = icepool.Die([1])
    assert result.equals(expected)


def test_map_fixed_point_1_cycle():

    def repl(outcome):
        if outcome >= 10:
            return outcome
        return outcome + icepool.Die([0, 1])

    result = icepool.Die([0]).map(repl, repeat='inf').simplify()
    assert result.equals(icepool.Die([10]))


def test_map_and_time() -> None:
    # How many coin flips until two heads?
    initial: icepool.Die[int] = icepool.Die([0])
    result = initial.map_and_time(lambda x: x if x >= 2 else x + coin(1, 2),
                                  repeat=100)
    assert float(result.marginals[1].mean()) == pytest.approx(4.0)


def test_mean_time_to_absorb() -> None:
    initial: icepool.Die[int] = icepool.Die([0])
    result = initial.mean_time_to_absorb(lambda x: x
                                         if x >= 2 else x + coin(1, 2))
    assert result == 4


def test_random_walk():

    def repl(x):
        if abs(x) >= 2:
            return x
        return icepool.Die([x - 1, x + 1])

    result = icepool.Die([0]).map(repl, repeat='inf').simplify()
    assert result.equals(icepool.Die([-2, 2]))


def test_random_walk_extra_arg():

    def repl(x, step):
        if abs(x) >= 2:
            return x
        else:
            return x + step

    result = icepool.map(repl, 0, Die([-1, 1]), repeat='inf').simplify()
    result2 = Die([0]).map(repl, Die([-1, 1]), repeat='inf').simplify()
    expected = Die([-2, 2])
    assert result == expected
    assert result2 == expected


def test_random_walk_biased():

    def repl(x):
        if abs(x) >= 2:
            return x
        return icepool.Die([x - 1, x + 1], times=[1, 2])

    result = icepool.Die([0]).map(repl, repeat='inf').simplify()
    assert result.equals(icepool.Die([-2, 2], times=[1, 4]))


def test_random_walk_biased_extra_arg():

    def repl(x, step):
        if abs(x) >= 2:
            return x
        else:
            return x + step

    result = icepool.map(repl, 0, Die([-1, 1, 1]), repeat='inf').simplify()
    result2 = Die([0]).map(repl, Die([-1, 1, 1]), repeat='inf').simplify()
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


def test_time_to_sum_d6():
    assert d6.mean_time_to_sum(10) == d6.time_to_sum(10, 11).mean()


def test_time_to_sum_d6_auto_max_time():
    assert d6.mean_time_to_sum(10) == d6.time_to_sum(10).mean()


def test_mean_time_to_sum_z6():
    cdf = []
    for i in range(11):
        cdf.append(i @ d(5) >= 10)
    expected = icepool.from_cumulative(range(11), cdf).mean() * Fraction(6, 5)
    assert (d6 - 1).mean_time_to_sum(10) == expected


def test_mean_time_to_sum_coin():
    assert icepool.coin(1, 2).mean_time_to_sum(10) == 20


def test_fractional_coin():
    assert icepool.coin(Fraction(1, 3)) == (icepool.d(3) == 1)


def test_stochastic_round():
    assert ((6 @ d6) / 2).stochastic_round().mean() == 10.5
    assert ((6 @ d6) / Fraction(3)).stochastic_round().mean() == 7


def test_map_and_time_extra_args():

    def test_function(current, roll):
        return min(current + roll, 10)

    result = Die([0]).map_and_time(test_function, d6, repeat=10)
    assert result.marginals[1].mean() == d6.mean_time_to_sum(10)


def test_map_and_time_extra_args_with_self_loops():

    def test_function(current, roll):
        return min(current + roll, 10)

    result = Die([0]).map_and_time(test_function, (d6 - 1), repeat=100)
    assert result.marginals[1].mean() == pytest.approx(
        (d6 - 1).mean_time_to_sum(10))


def test_map_time_limit():

    def test_function(current, roll):
        return min(current + roll, 10)

    assert Die([0]).map(test_function, d6,
                        repeat=10) == Die([0]).map(test_function,
                                                   d6,
                                                   repeat=20)


def test_group_by():
    result = d10.group_by(lambda x: x % 3)
    assert len(result) == 3
    assert result[0] == Die([3, 6, 9])
    assert result[1] == Die([1, 4, 7, 10])
    assert result[2] == Die([2, 5, 8])


def test_group_by_index():
    initial = Die([
        'aardvark',
        'alligator',
        'asp',
        'blowfish',
        'cat',
        'crocodile',
    ])
    result = initial.group_by[0]
    assert result['a'] == Die(['aardvark', 'alligator', 'asp'])
    assert result['b'] == Die(['blowfish'])
    assert result['c'] == Die(['cat', 'crocodile'])


def test_kwargs():

    def test(x, *, die):
        return x @ die

    assert d6.map(test, die=d6) == d6 @ d6
