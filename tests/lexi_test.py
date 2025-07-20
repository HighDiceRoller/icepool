import icepool
import pytest

from icepool import d6, Pool, Order

comparisons = ['==', '!=', '<=', '<', '>=', '>', 'cmp']


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [True, False, True, False, True, False, 0]))
def test_leximin_equal(order, comparison, expected):
    left = [1, 2, 3]
    right = [1, 2, 3]
    assert Pool(left).force_order(order).leximin(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, True, True, False, False, -1]))
def test_leximin_less(order, comparison, expected):
    left = [1, 2, 3, 4]
    right = [1, 3, 3, 3]
    assert Pool(left).force_order(order).leximin(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, False, False, True, True, 1]))
def test_leximin_greater(order, comparison, expected):
    left = [1, 3, 3, 3]
    right = [1, 2, 3, 4]
    assert Pool(left).force_order(order).leximin(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, False, False, True, True, 1]))
def test_leximin_equal_extra_left(order, comparison, expected):
    left = [1, 2, 3, 3]
    right = [1, 2, 3]
    assert Pool(left).force_order(order).leximin(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, True, True, False, False, -1]))
def test_leximin_less_extra_left(order, comparison, expected):
    left = [1, 2, 3, 4, 5]
    right = [1, 3, 3, 3]
    assert Pool(left).force_order(order).leximin(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, False, False, True, True, 1]))
def test_leximin_greater_extra_left(order, comparison, expected):
    left = [1, 3, 3, 3, 5]
    right = [1, 2, 3, 4]
    assert Pool(left).force_order(order).leximin(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, True, True, False, False, -1]))
def test_leximin_less_extra_right(order, comparison, expected):
    left = [1, 2, 3, 4]
    right = [1, 3, 3, 3, 5]
    assert Pool(left).force_order(order).leximin(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, False, False, True, True, 1]))
def test_leximin_greater_extra_right(order, comparison, expected):
    left = [1, 3, 3, 3]
    right = [1, 2, 3, 4, 5]
    assert Pool(left).force_order(order).leximin(comparison,
                                                 right).mode()[0] == expected
