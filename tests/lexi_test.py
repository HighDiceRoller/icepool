import icepool
import pytest

from icepool import d6, Pool, Order

comparisons = ['==', '!=', '<=', '<', '>=', '>', 'cmp']

# Leximin.


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
def test_leximin_equal_extra_right(order, comparison, expected):
    left = [1, 2, 3]
    right = [1, 2, 3, 3]
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


# Leximax.


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [True, False, True, False, True, False, 0]))
def test_leximax_equal(order, comparison, expected):
    left = [3, 2, 1]
    right = [3, 2, 1]
    assert Pool(left).force_order(order).leximax(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, True, True, False, False, -1]))
def test_leximax_less(order, comparison, expected):
    left = [3, 1, 1, 1]
    right = [3, 2, 1, 0]
    assert Pool(left).force_order(order).leximax(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, False, False, True, True, 1]))
def test_leximax_greater(order, comparison, expected):
    left = [3, 2, 1, 0]
    right = [3, 1, 1, 1]
    assert Pool(left).force_order(order).leximax(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, False, False, True, True, 1]))
def test_leximax_equal_extra_left(order, comparison, expected):
    left = [3, 2, 1, 1]
    right = [3, 2, 1]
    assert Pool(left).force_order(order).leximax(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, True, True, False, False, -1]))
def test_leximax_less_extra_left(order, comparison, expected):
    left = [3, 1, 1, 1]
    right = [3, 2, 1]
    assert Pool(left).force_order(order).leximax(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, False, False, True, True, 1]))
def test_leximax_greater_extra_left(order, comparison, expected):
    left = [3, 2, 1, 0]
    right = [3, 1, 1]
    assert Pool(left).force_order(order).leximax(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, True, True, False, False, -1]))
def test_leximax_equal_extra_right(order, comparison, expected):
    left = [3, 2, 1]
    right = [3, 2, 1, 1]
    assert Pool(left).force_order(order).leximax(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, True, True, False, False, -1]))
def test_leximax_less_extra_right(order, comparison, expected):
    left = [3, 1, 1]
    right = [3, 2, 1, 1]
    assert Pool(left).force_order(order).leximax(comparison,
                                                 right).mode()[0] == expected


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
@pytest.mark.parametrize(
    'comparison,expected',
    zip(comparisons, [False, True, False, False, True, True, 1]))
def test_leximax_greater_extra_right(order, comparison, expected):
    left = [3, 2, 1]
    right = [3, 1, 1, 1]
    assert Pool(left).force_order(order).leximax(comparison,
                                                 right).mode()[0] == expected
