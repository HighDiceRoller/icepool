import icepool
import pytest


def test_cartesian_product():
    result = icepool.Die([(icepool.d6, icepool.d6)])
    assert result.covariance(0, 1) == 0.0
    result_sum = result.sub(lambda x: sum(x))
    assert result_sum.equals(2 @ icepool.d6)


def test_cartesian_product_cast():
    result = icepool.Die([(icepool.d6, 2)])
    assert result.covariance(0, 1) == 0.0
    result_sum = result.sub(lambda x: sum(x))
    assert result_sum.equals(icepool.d6 + 2)


def test_vector_add():
    result = icepool.Die([(icepool.d8, 1)]) + icepool.Die([(0, icepool.d6)])
    expected = icepool.Die([(icepool.d8, icepool.d6 + 1)])
    assert result.equals(expected)


def test_vector_matmul():
    result = 2 @ icepool.Die([(icepool.d6, icepool.d8)])
    expected = icepool.Die([(2 @ icepool.d6, 2 @ icepool.d8)])
    assert result.equals(expected)


def test_nested_unary_elementwise():
    result = icepool.Die([(((1,),),)])
    result = -result
    assert result.marginals[0].marginals[0].marginals[0].equals(
        icepool.Die([-1]))


def test_nested_binary_elementwise():
    result = icepool.Die([(((icepool.d6,),),)])
    result = result + result
    assert result.marginals[0].marginals[0].marginals[0].equals(2 @ icepool.d6)


def test_binary_op_mismatch_scalar_vector():
    with pytest.raises(ValueError):
        result = icepool.d6 + icepool.Die([(icepool.d6, icepool.d8)])


def test_binary_op_mismatch_outcome_len():
    with pytest.raises(ValueError):
        result = icepool.Die([(icepool.d6, icepool.d8)]) + (1, 2, 3)


def test_sub_star():
    result = icepool.Die([(icepool.d6, icepool.d6)]).sub(lambda a, b: a + b,
                                                         star=1)
    expected = 2 @ icepool.d6
    assert result.equals(expected)


def test_reroll_star():
    result = icepool.Die([(icepool.d6, icepool.d6)])
    result = result.reroll(lambda a, b: a == 6 and b == 6, star=1)
    result = result.sub(lambda a, b: a + b, star=1)
    expected = (2 @ icepool.d6).reroll({12})
    assert result.equals(expected)


def test_reroll_until_star():
    result = icepool.Die([(icepool.d6, icepool.d6)])
    result = result.reroll_until(lambda a, b: a == 6 and b == 6, star=1)
    result = result.sub(lambda a, b: a + b, star=1)
    expected = (2 @ icepool.d6).reroll_until({12})
    assert result.equals(expected)


def test_explode_star():
    base = icepool.Die([(icepool.d6, icepool.d6)])
    result = base.explode(lambda a, b: a == 6 and b == 6, star=1)
    expected = base.explode()
    assert result.equals(expected)


def test_unpack_marginals():
    base = icepool.Die([(icepool.d6, icepool.d6)])
    a, b = base.marginals
    assert a == b
    assert a.simplify() == icepool.d6
