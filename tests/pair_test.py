import icepool
import operator
import pytest

from icepool import d4, d6, d8, Die, Order, map_function, Pool, multiset_function


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


def test_max_pair_example():
    result = Pool([6, 4, 3, 1]).max_pair_keep('<=', [5, 5], 'high').expand()
    assert result.simplify() == Die([(3, 4)])
    result = Pool([6, 4, 3, 1]).max_pair_drop('<=', [5, 5], 'high').expand()
    assert result.simplify() == Die([(1, 6)])


max_pair_ops = ['<=', '<', '>=', '>']


@pytest.mark.parametrize('op', max_pair_ops)
@pytest.mark.parametrize('priority', ['low', 'high'])
def test_max_pair_keep_size(op, priority):
    left = d6.pool(3)
    right = d6.pool(2)
    result = left.max_pair_keep(op, right, priority).size()
    complement = left.max_pair_drop(op, right, priority).size()

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

    expected = compute_expected(left, right)
    assert result == expected
    assert 3 - result == complement


pools_to_test = [d6.pool(2), d6.pool(3), Pool([d4, d6]), Pool([d4, d6, d8])]


@pytest.mark.parametrize('op', max_pair_ops)
@pytest.mark.parametrize('left', pools_to_test)
@pytest.mark.parametrize('right', pools_to_test)
def test_max_pair_expand_narrow(op, left, right):
    if op in ['<=', '<']:
        priority = 'high'
    else:
        priority = 'low'
    result = left.max_pair_keep(op, right, priority).expand()

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


@pytest.mark.parametrize('op', max_pair_ops)
@pytest.mark.parametrize('left', pools_to_test)
@pytest.mark.parametrize('right', pools_to_test)
def test_max_pair_expand_wide(op, left, right):
    if op in ['<=', '<']:
        priority = 'low'
    else:
        priority = 'high'
    result = left.max_pair_keep(op, right, priority).expand()

    @map_function
    def compute_expected(left, right):
        if op in ['>=', '>']:
            left = reversed(left)
            right = reversed(right)
        left = list(left)
        right = list(right)
        for size in range(min(len(left), len(right)), 0, -1):
            left_sublist = left[:size]
            right_sublist = right[-size:]
            if all(operators[op](l, r)
                   for l, r in zip(left_sublist, right_sublist)):
                return tuple(sorted(left_sublist))
        return ()

    expected = compute_expected(left, right)
    assert result == expected


@multiset_function
def sorcerer(win, lose):
    win_remaining = win.sort_pair_drop_while('==', lose)
    lose_remaining = lose.sort_pair_drop_while('==', win)
    return win_remaining.versus_all('>', lose_remaining).size()


@pytest.mark.parametrize('win,lose,victories', [
    ([10, 4, 4, 1], [8, 8, 6, 5, 2, 2], 1),
    ([10, 8, 8, 4, 3], [2, 2, 2, 1, 1, 1], 5),
    ([8, 7, 6, 1], [8, 5, 5, 2], 2),
    ([10, 10, 1], [9, 7, 2, 2], 2),
    ([10, 6, 6, 4], [6, 5, 4, 3], 1),
    ([9, 9, 1, 1], [8, 8, 2, 2], 2),
    ([7, 6, 5, 5], [4, 3, 2, 1], 4),
    ([10, 10, 8, 7, 7, 5], [10, 5, 5, 5], 4),
    ([9, 9, 6, 6, 5], [9, 9, 6, 6, 4], 1),
    ([9, 8, 5, 5, 2], [8, 5, 5, 2, 1], 1),
])
def test_sorcerer(win, lose, victories):
    assert sorcerer(win, lose).probability(victories) == 1


@multiset_function
def donjon(win, lose):
    return win.versus_all('>', lose.sort_pair_drop_while('==', win)).expand()


@pytest.mark.parametrize('win,lose,victories', [
    ([6, 12, 15, 18], [4, 7, 9, 11, 12], (15, 18)),
    ([3, 11, 12, 13, 15], [5, 8, 10, 13, 15], (11, 12, 13, 15)),
])
def test_donjon(win, lose, victories):
    assert donjon(win, lose).probability(victories) == 1
