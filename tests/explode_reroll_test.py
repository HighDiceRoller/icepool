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

"""
def test_explode_chance():
    result = hdroller.Die(hdroller.d10 >= 8).explode(3, {1 : 1/3})
    expected = hdroller.Die([1.0 - 0.3,
                    0.3 - 0.03,
                    0.03 - 0.003,
                    0.003 - 0.0003,
                    0.0003], 0)
    assert result.ks_stat(expected) == pytest.approx(0.0)

def test_explode_chance_weights():
    result = Die.mix([0]*7 + [1]*3).explode(3, {1 : 1/3})
    expected = hdroller.Die([1.0 - 0.3,
                    0.3 - 0.03,
                    0.03 - 0.003,
                    0.003 - 0.0003,
                    0.0003], 0)
    assert result.ks_stat(expected) == pytest.approx(0.0)
"""
    
def test_reroll():
    result = hdroller.d6.reroll(1)
    expected = hdroller.d5 + 1
    assert result.equals(expected)
    
def test_reroll_2():
    result = hdroller.d6.reroll(1, 2)
    expected = hdroller.d4 + 2
    assert result.equals(expected)

"""
def test_reroll_partial():
    result = hdroller.d4.reroll(outcomes={1 : 0.5})
    expected = [1/7, 2/7, 2/7, 2/7]
    assert result.pmf() == pytest.approx(expected, abs=abs_tol)
"""

def test_reroll_limit():
    result = hdroller.d4.reroll(1, max_depth=1)
    expected = hdroller.Die([1, 5, 5, 5], 1)
    assert result.equals(expected)

def test_infinite_reroll():
    assert len(hdroller.d4.reroll(1, 2, 3, 4)) == 0
