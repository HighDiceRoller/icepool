import _context

import hdroller
import pytest

def test_ks_stat_standard_dice():
    assert hdroller.d10.ks_stat(hdroller.d20) == pytest.approx(0.5)

def test_ks_stat_flat_number():
    assert hdroller.die(10).ks_stat(hdroller.die(10)) == 0.0
    assert hdroller.die(10).ks_stat(hdroller.die(9)) == 1.0
