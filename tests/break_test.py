import icepool
import pytest

from icepool import Break, d, map, coin, Die
from fractions import Fraction


def test_markov_chain_initial_break_result():

    def repl(x):
        if x <= 0 or x >= 3:
            return Break()
        return x + coin(1, 2)

    result = (d(6) - 3).map(repl, repeat='inf')
    assert result == Die([-2, -1, 0, 3, 3, 3])


def test_markov_chain_initial_break_mean_time_to_absorb():

    def repl(x):
        if x == 1:
            return Break()
        return x - coin(1, 2)

    result = d(10).mean_time_to_absorb(repl)
    assert result == Fraction(9, 2)
