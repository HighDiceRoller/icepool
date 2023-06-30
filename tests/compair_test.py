import icepool
import operator
import pytest

from icepool import d6, Die, Order, map_function


def test_risk():
    result = d6.pool(3).compair(d6.pool(2), '>')
    expected = Die({0: 2275, 1: 2611, 2: 2890})
    assert result == expected


def test_risk_ascending():
    result = d6.pool(3).compair(d6.pool(2), '<', order=Order.Ascending)
    expected = Die({0: 2275, 1: 2611, 2: 2890})
    assert result == expected


ops = [
    (operator.lt, '<'),
    (operator.le, '<='),
    (operator.gt, '>'),
    (operator.ge, '>='),
    (operator.eq, '=='),
    (operator.ne, '!='),
]


@pytest.mark.parametrize('op,name', ops)
def test_operators(op, name):
    result = d6.pool(3).compair(d6.pool(2), name)

    @map_function
    def compute_expected(left, right):
        result = 0
        for l, r in zip(left, right):
            if op(l, r):
                result += 1
        return result

    expected = compute_expected(d6.pool(3), d6.pool(2))
    assert result == expected


@pytest.mark.parametrize('op,name', ops)
def test_operators_extra_left(op, name):
    result = d6.pool(3).compair(d6.pool(2), name, extra_left=1)

    @map_function
    def compute_expected(left, right):
        result = 0
        for l, r in zip(left, right):
            if op(l, r):
                result += 1
        return result

    expected = compute_expected(d6.pool(3), d6.pool(2)) + 1
    assert result == expected


@pytest.mark.parametrize('op,name', ops)
def test_operators_extra_right(op, name):
    result = d6.pool(2).compair(d6.pool(3), name, extra_right=-1)

    @map_function
    def compute_expected(left, right):
        result = 0
        for l, r in zip(left, right):
            if op(l, r):
                result += 1
        return result

    expected = compute_expected(d6.pool(2), d6.pool(3)) - 1
    assert result == expected


@pytest.mark.parametrize('op,name', ops)
def test_operators_ascending(op, name):
    result = d6.pool(3).compair(d6.pool(2), name, order=Order.Ascending)

    @map_function
    def compute_expected(left, right):
        result = 0
        for l, r in zip(reversed(left), reversed(right)):
            if op(l, r):
                result += 1
        return result

    expected = compute_expected(d6.pool(3), d6.pool(2))
    assert result == expected
