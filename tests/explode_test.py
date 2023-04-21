import icepool
import pytest

abs_tol = 1e-9


def bf_explode_basic(die, depth):

    def func(*outcomes):
        result = 0
        for outcome in outcomes:
            result += outcome
            if outcome < die.max_outcome():
                break
        return result

    return icepool.die_map(func, *([die] * (depth + 1)))


@pytest.mark.parametrize('depth', range(6))
def test_explode_d6(depth):
    result = icepool.d6.explode(depth=depth)
    result_int = icepool.d6.explode(which=[6], depth=depth)
    expected = bf_explode_basic(icepool.d6, depth)
    assert result.equals(expected)
    assert result_int.equals(expected)


@pytest.mark.parametrize('depth', range(6))
def test_explode_multiple_weight(depth):
    result = icepool.d6.explode(which=[5, 6], depth=depth)
    assert result.denominator() == 6**(depth + 1)
