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
    """Test three different types of self-loop."""

    def repl(x, y):
        if y == 1:
            return Break()
        elif y == 2:
            return x
        else:
            return Reroll

    assert mean_time_to_absorb(repl, 0, d(3)) == 0


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


def test_restart_mean_time_to_absorb():

    def repl(x, y):
        if x == 10:
            return Break()
        elif y == 1:
            return Restart
        else:
            return x + 1

    assert mean_time_to_absorb(repl, 0, d(2)) == 10
