import operator
import icepool
import pytest

from icepool import d6, Pool
from icepool.population.die import Die


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
