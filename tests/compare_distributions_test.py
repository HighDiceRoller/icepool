import _context

from hdroller import Die
import pytest

def test_ks_stat_standard_dice():
    assert Die.d10.ks_stat(Die.d20) == pytest.approx(0.5)
