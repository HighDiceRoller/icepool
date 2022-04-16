import _context

import icepool
import pytest

"""
Tests empty dice.
"""

empty_dice = [icepool.Die(), icepool.Die(icepool.Reroll), icepool.Die({})]

@pytest.mark.parametrize('die', empty_dice)
def test_create_empty(die):
    result = die
    assert result.is_empty()
    assert result.ndim() == 'empty'

def test_op_empty():
    result = icepool.d6 + {}
    expected = icepool.Die()
    assert result.equals(expected)

def test_mix_empty():
    result = icepool.Die(icepool.d6, {})
    expected = icepool.d6
    assert result.equals(expected)
