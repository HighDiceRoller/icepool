import icepool
import pytest

from icepool import Break, d, map, coin, Die, Reroll, map_and_time, mean_time_to_absorb, Restart
from fractions import Fraction


def test_self_loop_types():
    """Test three different types of self-loop."""

    def repl(x, y):
        if y == 1:
            return Break()
        elif y == 2:
            return x
        else:
            return Reroll

    assert map_and_time(repl, 0, d(3), repeat=10).marginals[1].mean() == 0


def test_self_loop_types_mean_type_to_absorb():
    """Test four different types of self-loop."""

    def repl(x, y):
        if y == 1:
            return Break()
        elif y == 2:
            return x
        elif y == 3:
            return Break(x)
        else:
            return Reroll

    assert mean_time_to_absorb(repl, 0, d(4)) == 0


def test_break_value_repeat():

    def repl(x, y):
        if x >= 6:
            return Break(-1)
        return x + y

    result = map(repl, 0, d(2), repeat=10)
    assert result.probability(-1) == 1


def test_break_value_repeat_inf():

    def repl(x, y):
        if x >= 6:
            return Break(-1)
        return x + y

    result = map(repl, 0, coin(1, 2), repeat='inf')
    assert result.probability(-1) == 1


def test_initial_break_repeat_inf():

    def repl(x):
        if x <= 0 or x >= 3:
            return Break()
        return x + coin(1, 2)

    result = (d(6) - 3).map(repl, repeat='inf')
    assert result == Die([-2, -1, 0, 3, 3, 3])


def test_initial_break_mean_time_to_absorb():

    def repl(x):
        if x == 1:
            return Break()
        return x - coin(1, 2)

    result = d(10).mean_time_to_absorb(repl)
    assert result == 9


def test_restart_break():

    def repl(x, y):
        if x == 3:
            return Break()
        elif y == 1:
            return Restart
        elif y == 2:
            return Break()
        else:
            return x + 1

    result = map(repl, 0, d(3), repeat='inf')
    assert result == icepool.Die({0: 9, 1: 3, 2: 1, 3: 1})


def test_break_example():

    def example(total, new_roll):
        if total >= 10:
            return Break()  # same as Break(total)
        else:
            return total + new_roll

    result = map(example, 0, d(6), repeat=20)
    assert set(result.outcomes()) == {10, 11, 12, 13, 14, 15}


@pytest.mark.parametrize('repeat', [1, 3, 'inf'])
def test_break_reroll_repeat(repeat):
    # Break(Reroll) should behave like Reroll rather than raise.
    result = map(lambda x: Break(Reroll) if x == 1 else x + 1,
                 0,
                 repeat=repeat)
    expected = map(lambda x: Reroll if x == 1 else x + 1, 0, repeat=repeat)
    assert result == expected


@pytest.mark.parametrize('repeat', [1, 2, 'inf'])
def test_break_reroll_repeat_d6(repeat):

    def f(x, y):
        if y == 1:
            return Break(Reroll)
        return Break(x + y)

    assert map(f, 0, d(6), repeat=repeat) == map(f, 0, d(6))
