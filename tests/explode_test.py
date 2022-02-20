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
    result = hdroller.d6.explode(max_depth=max_depth)
    result_int = hdroller.d6.explode(outcomes=[6], max_depth=max_depth)
    expected = bf_explode_basic(hdroller.d6, max_depth)
    assert result.equals(expected)
    assert result_int.equals(expected)

@pytest.mark.parametrize('max_depth', range(6))
def test_explode_multiple_weight(max_depth):
    result = hdroller.d6.explode(outcomes=[5, 6], max_depth=max_depth)
    assert result.total_weight() == 6 ** (max_depth + 1)
