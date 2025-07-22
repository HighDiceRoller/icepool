import icepool
import operator
import pytest

from icepool import d4, d6, d8, Die, Order, map_function, Pool


def test_sort_pair_example_1():
    without_highest = Pool([6, 4, 3]).sort_pair('>', [5, 5]).expand()
    assert without_highest.simplify() == Die([(6, )])


def test_sort_pair_example_2():
    with_highest = Pool([6, 4, 3]).sort_pair('>', [5, 5],
                                             extra='keep').expand().simplify()
    assert with_highest == Die([(3, 6)])


def test_risk():
    result = d6.pool(3).highest(2).sort_pair('>', d6.pool(2)).size()
    expected = Die({0: 2275, 1: 2611, 2: 2890})
    assert result == expected


def test_risk_ascending():
    result = d6.pool(3).highest(2).sort_pair('>',
                                             d6.pool(2),
                                             order=Order.Ascending).size()
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
@pytest.mark.parametrize('use_drop', [False, True])
def test_sort_pair_operators(op, use_drop):
    if use_drop:
        result = d6.pool(3).sort_pair(op, d6.pool(2), extra='drop').size()
    else:
        result = d6.pool(3).highest(2).sort_pair(op, d6.pool(2)).size()

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
@pytest.mark.parametrize('use_drop', [False, True])
def test_sort_pair_operators_ascending(op, use_drop):
    if use_drop:
        result = d6.pool(3).sort_pair(op,
                                      d6.pool(2),
                                      order=Order.Ascending,
                                      extra='drop').size()
    else:
        result = d6.pool(3).lowest(2).sort_pair(op,
                                                d6.pool(2),
                                                order=Order.Ascending).size()

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
def test_sort_pair_operators_expand(op, left, right):
    result = left.highest(2).sort_pair(op, right).expand()

    @map_function
    def compute_expected(left, right):
        result = []
        for l, r in zip(reversed(left), reversed(right)):
            if operators[op](l, r):
                result.append(l)
        return tuple(sorted(result))

    expected = compute_expected(left, right)
    assert result == expected


def test_maximum_pair_example():
    result = Pool([6, 4, 3, 1]).maximum_pair_highest('<=', [5, 5],
                                                     keep='unpaired').expand()
    assert result.simplify() == Die([(1, 6)])


maximum_ops = ['<=', '<', '>=', '>']


@pytest.mark.parametrize('op', maximum_ops)
def test_maximum_pair(op):
    if op in ['<=', '<']:
        result = d6.pool(3).maximum_pair_highest(op, d6.pool(2),
                                                 keep='paired').size()
        complement = d6.pool(3).maximum_pair_highest(op,
                                                     d6.pool(2),
                                                     keep='unpaired').size()
    else:
        result = d6.pool(3).maximum_pair_lowest(op, d6.pool(2),
                                                keep='paired').size()
        complement = d6.pool(3).maximum_pair_lowest(op,
                                                    d6.pool(2),
                                                    keep='unpaired').size()

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
def test_maximum_pair_expand(op, left, right):
    if op in ['<=', '<']:
        result = left.maximum_pair_highest(op, right, keep='paired').expand()
    else:
        result = left.maximum_pair_lowest(op, right, keep='paired').expand()

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
