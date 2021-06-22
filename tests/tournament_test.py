import _context

from hdroller import Die
import hdroller.tournament
import numpy
import pytest

def test_round_robin_score_equal():
    dice = [Die.d6] * 10
    expected = [0.5] * 10
    assert hdroller.tournament.round_robin_score(*dice) == pytest.approx(expected)

def test_round_robin_ascending_ints():
    dice = [Die(x) for x in range(10)]
    expected = [(0.5 + x) / 10.0 for x in range(10)]
    assert hdroller.tournament.round_robin_score(*dice) == pytest.approx(expected)
