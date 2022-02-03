import _context

import hdroller
import hdroller.tournament
import pytest

def test_round_robin_score_equal():
    dice = [hdroller.d6] * 10
    expected = [0.5] * 10
    assert hdroller.tournament.round_robin_score(*dice) == pytest.approx(expected)

def test_round_robin_ascending_ints():
    dice = [hdroller.Die(x) for x in range(10)]
    expected = [(0.5 + x) / 10.0 for x in range(10)]
    assert hdroller.tournament.round_robin_score(*dice) == pytest.approx(expected)
