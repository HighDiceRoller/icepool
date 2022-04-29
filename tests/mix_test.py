import _context

import icepool
import pytest

"""
Tests the mix functionality of icepool.Die() and its derivatives.
"""

def test_mix_d6_faces():
    result = icepool.Die(1, 2, 3, 4, 5, 6)
    expected = icepool.d6
    assert result.equals(expected)

def test_mix_identical():
    assert icepool.Die(icepool.d6, icepool.d6, icepool.d6, icepool.d6).pmf() == pytest.approx(icepool.d6.pmf())

def test_mix_weight():
    outcomes = range(2, 13)
    mix_weights = [1, 2, 3, 4, 5, 6, 5, 4, 3, 2, 1]
    result = icepool.Die(*outcomes, weights=mix_weights)
    expected = 2 @ icepool.d6
    assert result.equals(expected)
    
def test_mix_mixed():
    die = icepool.Die(icepool.d4, icepool.d6)
    assert die.pmf() == icepool.Die(weights=[5, 5, 5, 5, 2, 2], min_outcome=1).pmf()

def test_mix_reroll():
    result = icepool.Die(1,2,3,4,icepool.Reroll,icepool.Reroll)
    expected = icepool.d4
    assert result.equals(expected)

def test_mix_dict_reroll():
    data = {1:1, 2:1, 3:1, 4:1, icepool.Reroll:10}
    result = icepool.Die(data, data).reduce()
    expected = icepool.d4
    assert result.equals(expected)

expected_d6x1 = icepool.Die(weights=[6, 6, 6, 6, 6, 0, 1, 1, 1, 1, 1, 1], min_outcome=1).trim()

def test_sub_array():
    die = icepool.d6.sub([5, 4, 1, 2, 3, icepool.d6 + 6])
    assert die.pmf() == pytest.approx(expected_d6x1.pmf())

def test_sub_dict():
    die = icepool.d6.sub({6 : icepool.d6+6})
    assert die.pmf() == pytest.approx(expected_d6x1.pmf())

def test_sub_func():
    die = icepool.d6.sub(lambda x: icepool.d6 + 6 if x == 6 else 6 - x)
    assert die.pmf() == pytest.approx(expected_d6x1.pmf())

def test_sub_mix():
    result = icepool.d6.sub(lambda x: x if x >= 3 else icepool.Reroll)
    expected = icepool.d4 + 2
    assert result.equals(expected)

def test_sub_max_depth():
    result = (icepool.d8 - 1).sub(lambda x: x // 2, max_depth=2).reduce()
    expected = icepool.d2 - 1
    assert result.equals(expected)

def collatz(x):
    if x == 1:
        return 1
    elif x % 2:
        return x * 3 + 1
    else:
        return x // 2

def test_sub_fixed_point():
    # Collatz conjecture.
    result = icepool.d100.sub(collatz, max_depth=None).reduce()
    expected = icepool.Die(1)
    assert result.equals(expected)

def test_if_else():
    assert (icepool.d6 >= 4).if_else(icepool.d6, icepool.d6+6).equals(icepool.d12, reduce=True)
    assert (icepool.d6 - 3).if_else(True, False).equals(icepool.d6 != 6, reduce=True)
