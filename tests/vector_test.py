import icepool
import pytest

from icepool import d, d4, d6, d8, vectorize, Die, Vector
from collections import namedtuple


def test_cartesian_product():
    result = icepool.vectorize(d6, d6)
    assert result.covariance(0, 1) == 0.0
    result_sum = result.map(lambda x: sum(x))
    assert result_sum.equals(2 @ icepool.d6)


def test_cartesian_product_cast():
    result = icepool.vectorize(d6, 2)
    assert result.covariance(0, 1) == 0.0
    result_sum = result.map(lambda x: sum(x))
    assert result_sum.equals(icepool.d6 + 2)


def test_vector_add():
    result = icepool.vectorize(d8, 1) + icepool.vectorize(0, d6)
    expected = icepool.vectorize(d8, d6 + 1)
    assert result.equals(expected)


def test_vector_matmul():
    result = 2 @ icepool.vectorize(d6, d8)
    expected = icepool.vectorize(2 @ d6, 2 @ d8)
    assert result.equals(expected)


def test_nested_unary_elementwise():
    result = icepool.Die([vectorize(vectorize(vectorize(1, ), ), )])
    result = -result
    assert result.marginals[0].marginals[0].marginals[0].equals(
        icepool.Die([-1]))


def test_nested_binary_elementwise():
    result = icepool.Die([vectorize(vectorize(vectorize(1, ), ), )])
    result = result + result
    assert result.marginals[0].marginals[0].marginals[0].equals(
        icepool.Die([2]))


def test_binary_op_mismatch_outcome_len():
    with pytest.raises(IndexError):
        result = icepool.vectorize(d6, d8) + icepool.vectorize(1, 2, 3)


def test_map_star():
    result = icepool.vectorize(d6, d6).map(lambda a, b: a + b)
    expected = 2 @ icepool.d6
    assert result.equals(expected)


def test_reroll_star():
    result = icepool.vectorize(d6, d6)
    result = result.reroll(lambda a, b: a == 6 and b == 6)
    result = result.map(lambda a, b: a + b)
    expected = (2 @ icepool.d6).reroll({12})
    assert result.equals(expected)


def test_filter_star():
    result = icepool.vectorize(d6, d6)
    result = result.filter(lambda a, b: a == 6 and b == 6)
    result = result.map(lambda a, b: a + b)
    expected = (2 @ icepool.d6).filter({12})
    assert result.equals(expected)


def test_explode_star():
    base = icepool.vectorize(d6, d6)
    result = base.explode(lambda a, b: a == 6 and b == 6)
    expected = base.explode()
    assert result.equals(expected)


def test_unpack_marginals():
    base = icepool.vectorize(d6, d6)
    a, b = base.marginals
    assert a == b
    assert a.simplify() == icepool.d6


def test_one_hot():

    class OneHotEvaluator(icepool.MultisetEvaluator):

        def next_state(self, state, _, count):
            if state is None:
                state = ()
            return state + (count, )

        def final_outcome(self, final_state):
            return icepool.Vector(final_state)

        def alignment(self, *_):
            return [1, 2, 3, 4, 5, 6]

    result = 3 @ icepool.one_hot(6)
    expected = icepool.d6.pool(3).evaluate(evaluator=OneHotEvaluator())
    assert result == expected


def test_vector_scalar_mult():
    result = vectorize(d6, d8) * 2
    expected = vectorize(d6 * 2, d8 * 2)
    assert result == expected


def test_pool_vector_sum():
    result = vectorize(d6, d6).pool(2).sum()
    expected = vectorize(2 @ d6, 2 @ d6)
    assert result == expected


def test_vector_comparison():
    result = vectorize(d6, d6) > vectorize(0, 0)
    expected = Die([vectorize(True, True)], times=36)
    assert result == expected


def test_vector_append():
    assert Vector((1, 2)).append(3) == Vector((1, 2, 3))


def test_vector_concatenate():
    assert Vector((1, 2)).concatenate(range(2)) == Vector((1, 2, 0, 1))


def test_to_one_hot():
    assert d4.to_one_hot() == Die([
        Vector([1, 0, 0, 0]),
        Vector([0, 1, 0, 0]),
        Vector([0, 0, 1, 0]),
        Vector([0, 0, 0, 1]),
    ])


def test_named_tuple():
    Point = namedtuple('Point', ['x', 'y'])
    a = Point(0, 1)
    b = Point(1, 2)
    assert Die([a, b]).marginals.y == d(2)
