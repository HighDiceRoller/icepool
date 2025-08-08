import operator
import icepool
import pytest

from icepool import d6, Pool, Deck, Die, Order, multiset_function


def test_difference():
    result = (d6.pool(3) - d6.pool(1)).size()
    expected = icepool.highest(3 @ (d6 != 6), 2)
    assert result.simplify() == expected.simplify()


def test_difference_keep_negative_counts():
    result = d6.pool(3).difference(d6.pool(1),
                                   keep_negative_counts=True).size()
    assert result.probability(2) == 1


def test_intersection():
    result = (d6.pool(10) & {6: 5}).size()
    expected = icepool.lowest(10 @ (d6 == 6), 5)
    assert result == expected


def test_mul():
    result = (d6.pool(3) * 2).sum()
    expected = (3 @ d6) * 2
    assert result == expected


def test_multiple_union():
    result = d6.pool(1).union([6], [7]).sum()
    expected = d6 + 12
    assert result == expected


def test_multiple_intersection():
    result = d6.pool(1).intersection([d6], [d6]).sum()
    expected = (2 @ d6 == 12) * d6
    assert result == expected


ops_and_expected = [
    (operator.add, (1, 1, 2, 2, 2, 3, 4)),
    (operator.sub, (2, 3)),
    (operator.and_, (1, 2)),
    (operator.or_, (1, 2, 2, 3, 4)),
    (operator.xor, (2, 3, 4)),
]


@pytest.mark.parametrize('op,expected', ops_and_expected)
def test_operator_examples(op, expected):
    result = op(Pool([1, 2, 2, 3]), Pool([1, 2, 4])).expand(Order.Ascending)
    assert result == Die([expected])


@pytest.mark.parametrize('op,expected', ops_and_expected)
def test_operator_examples_deal(op, expected):
    result = op(Deck([1, 2, 2, 3]).deal(4),
                Deck([1, 2, 4]).deal(3)).expand(Order.Ascending)
    assert result == Die([expected])


def test_example_multiply_counts():
    result = (Pool([1, 2, 2, 3]) * 2).expand(Order.Ascending)
    expected = Die([(1, 1, 2, 2, 2, 2, 3, 3)])
    assert result == expected


def test_example_divide_counts():
    result = (Pool([1, 2, 2, 3]) // 2).expand(Order.Ascending)
    expected = Die([(2, )])
    assert result == expected


def test_example_keep_counts_le():
    result = Pool([1, 2, 2, 3, 3, 3]).keep_counts('<=',
                                                  2).expand(Order.Ascending)
    expected = Die([(1, 2, 2)])
    assert result == expected


def test_example_keep_counts_lt():
    result = Pool([1, 2, 2, 3, 3, 3]).keep_counts('<',
                                                  2).expand(Order.Ascending)
    expected = Die([(1, )])
    assert result == expected


def test_example_keep_counts_ge():
    result = Pool([1, 2, 2, 3, 3, 3]).keep_counts('>=',
                                                  2).expand(Order.Ascending)
    expected = Die([(2, 2, 3, 3, 3)])
    assert result == expected


def test_example_keep_counts_gt():
    result = Pool([1, 2, 2, 3, 3, 3]).keep_counts('>',
                                                  2).expand(Order.Ascending)
    expected = Die([(3, 3, 3)])
    assert result == expected


def test_example_keep_counts_eq():
    result = Pool([1, 2, 2, 3, 3, 3]).keep_counts('==',
                                                  2).expand(Order.Ascending)
    expected = Die([(2, 2)])
    assert result == expected


def test_example_keep_counts_ne():
    result = Pool([1, 2, 2, 3, 3, 3]).keep_counts('!=',
                                                  2).expand(Order.Ascending)
    expected = Die([(1, 3, 3, 3)])
    assert result == expected


def test_example_keep_counts_ge_using_map():
    result = Pool([1, 2, 2, 3]).map_counts(
        function=lambda o, c: c if c >= 2 else 0).expand(Order.Ascending)
    expected = Die([(2, 2)])
    assert result == expected


def test_example_unique():
    result = Pool([1, 2, 2, 3]).unique().expand(Order.Ascending)
    expected = Die([(1, 2, 3)])
    assert result == expected


def test_example_unique_using_map() -> None:
    result = Pool([1, 2, 2,
                   3]).map_counts(function=lambda _, c: min(c, 1)).expand(
                       Order.Ascending)
    expected = Die([(1, 2, 3)])
    assert result == expected


def test_example_intersect_using_map() -> None:

    def intersect(_, a, b):
        return min(a, b)

    result = Pool.map_counts(d6.pool(3), d6.pool(3), function=intersect).size()
    expected = (d6.pool(3) & d6.pool(3)).size()
    assert result == expected


def test_mod():

    @multiset_function
    def expected(x):
        return (x - (x // 2) * 2).expand()

    pool = d6.pool(4)
    assert (pool % 2).expand() == expected(pool)
