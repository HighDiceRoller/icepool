import icepool
import pytest

from icepool import d6, d8


def test_cartesian_product():
    result = icepool.cartesian_product(d6, d6)
    assert result.covariance(0, 1) == 0.0
    result_sum = result.map(lambda x: sum(x))
    assert result_sum.equals(2 @ icepool.d6)


def test_cartesian_product_constructor():
    result = icepool.Die([(d6, d6)])
    expected = icepool.cartesian_product(d6, d6)
    assert result == expected


def test_cartesian_product_cast():
    result = icepool.cartesian_product(d6, 2)
    assert result.covariance(0, 1) == 0.0
    result_sum = result.map(lambda x: sum(x))
    assert result_sum.equals(icepool.d6 + 2)


def test_vector_add():
    result = icepool.cartesian_product(d8, 1) + icepool.cartesian_product(0, d6)
    expected = icepool.cartesian_product(d8, d6 + 1)
    assert result.equals(expected)


def test_vector_matmul():
    result = 2 @ icepool.cartesian_product(d6, d8)
    expected = icepool.cartesian_product(2 @ d6, 2 @ d8)
    assert result.equals(expected)


def test_nested_unary_elementwise():
    result = icepool.Die([(((1,),),)])
    result = -result
    assert result.marginals[0].marginals[0].marginals[0].equals(
        icepool.Die([-1]))


def test_nested_binary_elementwise():
    result = icepool.Die([(((1,),),)])
    result = result + result
    assert result.marginals[0].marginals[0].marginals[0].equals(icepool.Die([2
                                                                            ]))


def test_binary_op_mismatch_scalar_vector():
    with pytest.raises(ValueError):
        result = icepool.d6 + icepool.cartesian_product(d6, d8)


def test_binary_op_mismatch_outcome_len():
    with pytest.raises(ValueError):
        result = icepool.cartesian_product(d6, d8) + (1, 2, 3)


def test_map_star():
    result = icepool.cartesian_product(d6, d6).map(lambda a, b: a + b, star=1)
    expected = 2 @ icepool.d6
    assert result.equals(expected)


def test_reroll_star():
    result = icepool.cartesian_product(d6, d6)
    result = result.reroll(lambda a, b: a == 6 and b == 6, star=1)
    result = result.map(lambda a, b: a + b, star=1)
    expected = (2 @ icepool.d6).reroll({12})
    assert result.equals(expected)


def test_filter_star():
    result = icepool.cartesian_product(d6, d6)
    result = result.filter(lambda a, b: a == 6 and b == 6, star=1)
    result = result.map(lambda a, b: a + b, star=1)
    expected = (2 @ icepool.d6).filter({12})
    assert result.equals(expected)


def test_explode_star():
    base = icepool.cartesian_product(d6, d6)
    result = base.explode(lambda a, b: a == 6 and b == 6, star=1)
    expected = base.explode()
    assert result.equals(expected)


def test_unpack_marginals():
    base = icepool.cartesian_product(d6, d6)
    a, b = base.marginals
    assert a == b
    assert a.simplify() == icepool.d6


def test_one_hot():

    class OneHotEvaluator(icepool.OutcomeCountEvaluator):

        def next_state(self, state, _, count):
            if state is None:
                state = ()
            return state + (count,)

        def alignment(self, *_):
            return [1, 2, 3, 4, 5, 6]

    result = 3 @ icepool.one_hot(6)
    expected = icepool.d6.pool(3).evaluate(OneHotEvaluator())
    assert result == expected
