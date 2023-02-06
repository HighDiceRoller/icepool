import operator
import icepool
import pytest

from icepool import d6, Pool, Deck, Die


def test_difference():
    result = (d6.pool(3) - d6.pool(1)).count()
    expected = icepool.highest(3 @ (d6 != 6), 2)
    assert result.simplify() == expected.simplify()


def test_intersection():
    result = (d6.pool(10) & {6: 5}).count()
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
    result = op(Pool([1, 2, 2, 3]), Pool([1, 2, 4])).expand()
    assert result == Die([expected])


@pytest.mark.parametrize('op,expected', ops_and_expected)
def test_operator_examples_deal(op, expected):
    result = op(Deck([1, 2, 2, 3]).deal(4), Deck([1, 2, 4]).deal(3)).expand()
    assert result == Die([expected])


def test_example_multiply_counts():
    expected = (Pool([1, 2, 2, 3]) * 2).expand()
    result = Die([(1, 1, 2, 2, 2, 2, 3, 3)])
    assert result == Die([expected])


def test_example_divide_counts():
    expected = (Pool([1, 2, 2, 3]) // 2).expand()
    result = Die([(2,)])
    assert result == Die([expected])


def test_example_filter_counts():
    expected = Pool([1, 2, 2, 3]).filter_counts(2).expand()
    result = Die([(2, 2)])
    assert result == Die([expected])


def test_example_filter_counts_using_map():
    expected = Pool([1, 2, 2,
                     3]).map_counts(lambda o, c: c if c >= 2 else 0).expand()
    result = Die([(2, 2)])
    assert result == Die([expected])


def test_example_unique():
    expected = Pool([1, 2, 2, 3]).unique().expand()
    result = Die([(1, 2, 3)])
    assert result == Die([expected])


def test_example_unique_using_map() -> None:
    expected = Pool([1, 2, 2, 3]).map_counts(lambda c: min(c, 1)).expand()
    result = Die([(1, 2, 3)])
    assert result == Die([expected])
