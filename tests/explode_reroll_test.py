import _context

from hdroller import Die
import pytest

abs_tol = 1e-9

def bf_explode_basic(die, max_times):
    def func(*outcomes):
        result = 0
        for outcome in outcomes:
            result += outcome
            if outcome < die.max_outcome(): break
        return result
    return Die.combine(*([die] * (max_times+1)), func=func)

@pytest.mark.parametrize('max_times', range(6))
def test_explode_d6(max_times):
    result = Die.d6.explode(max_times)
    result_int = Die.d6.explode(max_times, outcomes=6)
    result_list = Die.d6.explode(max_times, outcomes=[6])
    expected = bf_explode_basic(Die.d6, max_times)
    assert result.pmf() == pytest.approx(expected.pmf(), abs=abs_tol)
    assert result_int.pmf() == pytest.approx(expected.pmf(), abs=abs_tol)
    assert result_list.pmf() == pytest.approx(expected.pmf(), abs=abs_tol)

def test_explode_chance():
    result = Die(Die.d10 >= 8).explode(3, {1 : 1/3})
    expected = Die([1.0 - 0.3,
                    0.3 - 0.03,
                    0.03 - 0.003,
                    0.003 - 0.0003,
                    0.0003], 0)
    assert result.ks_stat(expected) == pytest.approx(0.0)

def test_explode_chance_weights():
    result = Die.mix([0]*7 + [1]*3).explode(3, {1 : 1/3})
    expected = Die([1.0 - 0.3,
                    0.3 - 0.03,
                    0.03 - 0.003,
                    0.003 - 0.0003,
                    0.0003], 0)
    assert result.ks_stat(expected) == pytest.approx(0.0)
    
def test_reroll():
    result = Die.d6.reroll(outcomes=1)
    expected = Die.d5 + 1
    assert result.pmf() == pytest.approx(expected.pmf(), abs=abs_tol)
    
def test_reroll_2():
    result = Die.d6.reroll(outcomes=[1, 2])
    expected = Die.d4 + 2
    assert result.pmf() == pytest.approx(expected.pmf(), abs=abs_tol)

def test_reroll_partial():
    result = Die.d4.reroll(outcomes={1 : 0.5})
    expected = [1/7, 2/7, 2/7, 2/7]
    assert result.pmf() == pytest.approx(expected, abs=abs_tol)

def test_reroll_limit():
    result = Die.d4.reroll(outcomes=1, max_times=1)
    expected = [1/16, 5/16, 5/16, 5/16]
    assert result.pmf() == pytest.approx(expected, abs=abs_tol)