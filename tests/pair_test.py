import icepool
import operator
import pytest

from icepool import d6, Die, Order, map_function


def test_risk():
    result = d6.pool(3).compair_gt(d6.pool(2))
    expected = Die({0: 2275, 1: 2611, 2: 2890})
    assert result == expected


def test_risk_ascending():
    result = d6.pool(3).compair_lt(d6.pool(2), order=Order.Ascending)
    expected = Die({0: 2275, 1: 2611, 2: 2890})
    assert result == expected


ops = ['lt', 'le', 'gt', 'ge', 'eq', 'ne']


@pytest.mark.parametrize('op', ops)
def test_operators(op):

    result = getattr(d6.pool(3), 'compair_' + op)(d6.pool(2))

    @map_function
    def compute_expected(left, right):
        result = 0
        for l, r in zip(reversed(left), reversed(right)):
            if getattr(operator, op)(l, r):
                result += 1
        return result

    expected = compute_expected(d6.pool(3), d6.pool(2))
    assert result == expected


@pytest.mark.parametrize('op', ops)
def test_operators_ascending(op):
    result = getattr(d6.pool(3), 'compair_' + op)(d6.pool(2),
                                                  order=Order.Ascending)

    @map_function
    def compute_expected(left, right):
        result = 0
        for l, r in zip(left, right):
            if getattr(operator, op)(l, r):
                result += 1
        return result

    expected = compute_expected(d6.pool(3), d6.pool(2))
    assert result == expected
