import icepool
import pytest
"""
Tests empty dice.
"""

empty_dice = [icepool.Die([]), icepool.Die([icepool.Reroll]), icepool.Die({})]


@pytest.mark.parametrize('die', empty_dice)
def test_create_empty(die):
    result = die
    assert result.is_empty()


def test_op_empty():
    result = icepool.d6 + icepool.Die([])
    expected = icepool.Die([])
    assert result.equals(expected)


def test_mix_empty():
    result = icepool.Die([icepool.d6, icepool.Die({})])
    expected = icepool.d6
    assert result.equals(expected)


def test_apply_empty():
    result = icepool.apply(lambda x, y: 0, icepool.Die({}), icepool.Die({}))
    expected = icepool.Die({})
    assert result.equals(expected)


def test_zero_die_standard_pool():
    assert icepool.standard_pool([]).sum() == icepool.Die([0])
