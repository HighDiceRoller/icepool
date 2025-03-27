import icepool
import operator
import pytest

from icepool import d4, d6, d8, Die, Order, map_function, Pool


def test_sort_match_example():
    without_highest = Pool([6, 4, 3]).sort_match('>', [5, 5]).expand()
    assert without_highest.simplify() == Die([(3, 6)])
    with_highest = Pool([6, 4,
                         3]).highest(2).sort_match('>',
                                                   [5, 5]).expand().simplify()
    assert with_highest == Die([(6, )])


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


@pytest.mark.parametrize('op', sort_ops)
@pytest.mark.parametrize('left', [d6.pool(2), d6.pool(3), Pool([d4, d6, d8])])
@pytest.mark.parametrize('right', [d6.pool(2), Pool([d4, d6])])
def test_sort_match_operators_expand(op, left, right):
    result = left.highest(2).sort_match(op, right).expand()

    @map_function
    def compute_expected(left, right):
        result = []
        for l, r in zip(reversed(left), reversed(right)):
            if operators[op](l, r):
                result.append(l)
        return tuple(sorted(result))

    expected = compute_expected(left, right)
    assert result == expected


def test_maximum_match_example():
    result = Pool([6,
                   4, 3, 1]).maximum_match_highest('<=', [5, 5],
                                                   keep='unmatched').expand()
    assert result.simplify() == Die([(1, 6)])


maximum_ops = ['<=', '<', '>=', '>']


@pytest.mark.parametrize('op', maximum_ops)
def test_maximum_match(op):
    if op in ['<=', '<']:
        result = d6.pool(3).maximum_match_highest(op,
                                                  d6.pool(2),
                                                  keep='matched').count()
        complement = d6.pool(3).maximum_match_highest(
            op, d6.pool(2), keep='unmatched').count()
    else:
        result = d6.pool(3).maximum_match_lowest(op,
                                                 d6.pool(2),
                                                 keep='matched').count()
        complement = d6.pool(3).maximum_match_lowest(op,
                                                     d6.pool(2),
                                                     keep='unmatched').count()

    @map_function
    def compute_expected(left, right):
        if op in ['<=', '<']:
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
                left.pop(0)
        return result

    expected = compute_expected(d6.pool(3), d6.pool(2))
    assert result == expected
    assert 3 - result == complement


@pytest.mark.parametrize('op', maximum_ops)
@pytest.mark.parametrize('left', [d6.pool(2), d6.pool(3), Pool([d4, d6, d8])])
@pytest.mark.parametrize('right', [d6.pool(2), Pool([d4, d6])])
def test_maximum_match_expand(op, left, right):
    if op in ['<=', '<']:
        result = left.maximum_match_highest(op, right, keep='matched').expand()
    else:
        result = left.maximum_match_lowest(op, right, keep='matched').expand()

    @map_function
    def compute_expected(left, right):
        if op in ['<=', '<']:
            left = reversed(left)
            right = reversed(right)
        left = list(left)
        right = list(right)
        result = []
        while left and right:
            if operators[op](left[0], right[0]):
                result.append(left[0])
                left.pop(0)
                right.pop(0)
            else:
                left.pop(0)
        return tuple(sorted(result))

    expected = compute_expected(left, right)
    assert result == expected
