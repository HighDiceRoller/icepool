import _context

import icepool
import pytest

from icepool import FindBestRun

# no wraparound
find_best_run = FindBestRun()

def test_poker_straight():
    draws = icepool.Deck(range(13), times=4).draws(5)
    result = find_best_run.eval(draws).marginals[0] == 5
    assert result.equals(icepool.coin(9216, 2598960))
