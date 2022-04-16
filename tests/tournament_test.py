import _context

import icepool
import icepool.tournament
import pytest

def test_round_robin_score_equal():
    dice = [icepool.d6] * 10
    expected = [0.5] * 10
    assert icepool.tournament.round_robin_score(*dice) == pytest.approx(expected)

def test_round_robin_ascending_ints():
    dice = [icepool.Die(x) for x in range(10)]
    expected = [(0.5 + x) / 10.0 for x in range(10)]
    assert icepool.tournament.round_robin_score(*dice) == pytest.approx(expected)
