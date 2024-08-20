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


operators = {
    '==': operator.eq,
    '!=': operator.ne,
    '<=': operator.le,
    '<': operator.lt,
    '>=': operator.ge,
    '>': operator.gt,
}

sort_ops = ['==', '!=', '<=', '<', '>=', '>']


@pytest.mark.parametrize('op', sort_ops)
def test_sort_match_operators(op):
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


@pytest.mark.parametrize('op', sort_ops)
def test_sort_match_operators_ascending(op):
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


maximum_ops = ['<=', '<', '>=', '>']


@pytest.mark.parametrize('op', maximum_ops)
def test_maximum_match(op):
    result = d6.pool(3).maximum_match(op, d6.pool(2), keep='matched').count()
    complement = d6.pool(3).maximum_match(op, d6.pool(2),
                                          keep='unmatched').count()

    @map_function
    def compute_expected(left, right):
        if op in ['>=', '>']:
            left = reversed(left)
            right = reversed(right)
        left = list(left)
        right = list(right)
        result = 0
        while left and right:
            if operators[op](left[0], right[0]):
                result += 1
                left.pop(0)
                right.pop(0)
            else:
                right.pop(0)
        return result

    expected = compute_expected(d6.pool(3), d6.pool(2))
    assert result == expected
    assert 3 - result == complement
