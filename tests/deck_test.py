import _context

import icepool
import pytest

from icepool import FindBestRun

# no wraparound
find_best_run = FindBestRun()

def test_poker_straight():
    deck = icepool.Deck(range(13), dups=[4]*13, hand_size=5)
    result = find_best_run.eval(deck)[0] == 5
    assert result.equals(icepool.coin(9216, 2598960))
