import _context

from hdroller import Die
import pytest

def test_ks_stat_standard_dice():
    assert Die.d10.ks_stat(Die.d20) == pytest.approx(0.5)

def test_ks_stat_flat_number():
    assert Die(10).ks_stat(Die(10)) == 0.0
    assert Die(10).ks_stat(Die(9)) == 1.0
