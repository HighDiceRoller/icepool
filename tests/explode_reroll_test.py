import _context

import hdroller
import pytest

abs_tol = 1e-9

def bf_explode_basic(die, max_depth):
    def func(*outcomes):
        result = 0
        for outcome in outcomes:
            result += outcome
            if outcome < die.max_outcome(): break
        return result
    return hdroller.apply(func, *([die] * (max_depth+1)))

@pytest.mark.parametrize('max_depth', range(6))
def test_explode_d6(max_depth):
    result = hdroller.d6.explode(max_depth)
    result_int = hdroller.d6.explode(max_depth, outcomes=[6])
    expected = bf_explode_basic(hdroller.d6, max_depth)
    assert result.equals(expected)
    assert result_int.equals(expected)

@pytest.mark.parametrize('max_depth', range(6))
def test_explode_multiple_weight(max_depth):
    result = hdroller.d6.explode(max_depth, outcomes=[5, 6])
    assert result.total_weight() == 6 ** (max_depth + 1)
    
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
    expected = hdroller.Die([1, 5, 5, 5], min_outcome=1)
    assert result.equals(expected)
    
def test_reroll_until_limit():
    result = hdroller.d4.reroll_until([2, 3, 4], max_depth=1)
    expected = hdroller.Die([1, 5, 5, 5], min_outcome=1)
    assert result.equals(expected)

def test_reroll_func():
    result = hdroller.d4.reroll(lambda x: x == 1, max_depth=1)
    expected = hdroller.Die([1, 5, 5, 5], min_outcome=1)
    assert result.equals(expected)

def test_reroll_until_func():
    result = hdroller.d4.reroll_until(lambda x: x != 1, max_depth=1)
    expected = hdroller.Die([1, 5, 5, 5], min_outcome=1)
    assert result.equals(expected)

def test_infinite_reroll():
    assert hdroller.d4.reroll([1, 2, 3, 4]).num_outcomes() == 0

