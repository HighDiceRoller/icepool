import _context

import hdroller
import pytest

"""
Tests empty dice.
"""

empty_dice = [hdroller.Die(), hdroller.Die(hdroller.Reroll), hdroller.Die({})]

@pytest.mark.parametrize('die', empty_dice)
def test_create_empty(die):
    result = die
    assert result.is_empty()
    assert result.ndim() == 'empty'

def test_op_empty():
    result = hdroller.d6 + {}
    expected = hdroller.Die()
    assert result.equals(expected)

def test_mix_empty():
    result = hdroller.Die(hdroller.d6, {})
    expected = hdroller.d6
    assert result.equals(expected)
