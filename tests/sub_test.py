import _context

import icepool
import pytest

expected_d6x1 = icepool.Die(*range(1, 13), weights=[6, 6, 6, 6, 6, 0, 1, 1, 1, 1, 1, 1]).trim()

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
    result = (icepool.d8 - 1).sub(lambda x: x // 2, max_depth=2).reduce_weights()
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
    result = icepool.d100.sub(collatz, max_depth=None).reduce_weights()
    expected = icepool.Die(1)
    assert result.equals(expected)
    
def test_sub_extra_args():
    def sub_plus_die(outcome, die):
        return outcome + die
        
    result = icepool.d6.sub(sub_plus_die, icepool.d6)
    expected = 2 @ icepool.d6
    assert result.equals(expected)
