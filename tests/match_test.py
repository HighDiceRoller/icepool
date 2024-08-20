import icepool
import operator
import pytest

from icepool import d6, Die, Order, map_function


def test_risk():
    result = d6.pool(3).highest(2).sort_match('>', d6.pool(2)).count()
    expected = Die({0: 2275, 1: 2611, 2: 2890})
    assert result == expected


def test_risk_ascending():
    result = d6.pool(3).highest(2).sort_match('>',
                                              d6.pool(2),
                                              order=Order.Ascending).count()
    expected = Die({0: 2275, 1: 2611, 2: 2890})
    assert result == expected


ops = ['==', '!=', '<=', '<', '>=', '>']

operators = {
    '==': operator.eq,
    '!=': operator.ne,
    '<=': operator.le,
    '<': operator.lt,
    '>=': operator.ge,
    '>': operator.gt,
}


@pytest.mark.parametrize('op', ops)
def test_operators(op):
    result = d6.pool(3).highest(2).sort_match(op, d6.pool(2)).count()

    @map_function
    def compute_expected(left, right):
        result = 0
        for l, r in zip(reversed(left), reversed(right)):
            if operators[op](l, r):
                result += 1
        return result

    expected = compute_expected(d6.pool(3), d6.pool(2))
    assert result == expected


@pytest.mark.parametrize('op', ops)
def test_operators_ascending(op):
    result = d6.pool(3).lowest(2).sort_match(op,
                                             d6.pool(2),
                                             order=Order.Ascending).count()

    @map_function
    def compute_expected(left, right):
        result = 0
        for l, r in zip(left, right):
            if operators[op](l, r):
                result += 1
        return result

    expected = compute_expected(d6.pool(3), d6.pool(2))
    assert result == expected
