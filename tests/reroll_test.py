import _context

import hdroller
import pytest

def test_reroll_default():
    result = hdroller.d6.reroll()
    expected = hdroller.d5 + 1
    assert result.equals(expected)

def test_reroll():
    result = hdroller.d6.reroll([1])
    expected = hdroller.d5 + 1
    assert result.equals(expected)
    
def test_reroll_2():
    result = hdroller.d6.reroll([1, 2])
    expected = hdroller.d4 + 2
    assert result.equals(expected)

"""
def test_reroll_partial():
    result = hdroller.d4.reroll(outcomes={1 : 0.5})
    expected = [1/7, 2/7, 2/7, 2/7]
    assert result.pmf() == pytest.approx(expected, abs=abs_tol)
"""

def test_reroll_limit():
    result = hdroller.d4.reroll([1], max_depth=1)
    expected = hdroller.Die(weights=[1, 5, 5, 5], min_outcome=1)
    assert result.equals(expected)
    
def test_reroll_until_limit():
    result = hdroller.d4.reroll_until([2, 3, 4], max_depth=1)
    expected = hdroller.Die(weights=[1, 5, 5, 5], min_outcome=1)
    assert result.equals(expected)

def test_reroll_func():
    result = hdroller.d4.reroll(lambda x: x == 1, max_depth=1)
    expected = hdroller.Die(weights=[1, 5, 5, 5], min_outcome=1)
    assert result.equals(expected)

def test_reroll_until_func():
    result = hdroller.d4.reroll_until(lambda x: x != 1, max_depth=1)
    expected = hdroller.Die(weights=[1, 5, 5, 5], min_outcome=1)
    assert result.equals(expected)

def test_infinite_reroll():
    assert hdroller.d4.reroll([1, 2, 3, 4]).num_outcomes() == 0

def test_reroll_multidim():
    result = hdroller.Die((1, 0), (0, 1)).reroll(lambda a, b: a == 0)
    expected = hdroller.Die((1, 0))
    assert result.equals(expected)

def test_reroll_until_multidim():
    result = hdroller.Die((1, 0), (0, 1)).reroll_until(lambda a, b: a == 0)
    expected = hdroller.Die((0, 1))
    assert result.equals(expected)
