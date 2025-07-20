import icepool
import pytest

from icepool import d6, Pool, Order


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
def test_versus_all_ge(order):
    assert Pool([1, 2, 3]).versus_all('>=',
                                      [1, 2]).expand().mode()[0] == (2, 3)


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
def test_versus_all_gt(order):
    assert Pool([1, 2, 3]).versus_all('>', [1, 2]).expand().mode()[0] == (3, )


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
def test_versus_all_le(order):
    assert Pool([1, 2, 3]).versus_all('<=',
                                      [2, 3]).expand().mode()[0] == (1, 2)


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
def test_versus_all_lt(order):
    assert Pool([1, 2, 3]).versus_all('<', [2, 3]).expand().mode()[0] == (1, )


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
def test_versus_any_ge(order):
    assert Pool([1, 2, 3]).versus_any('>=',
                                      [2, 3]).expand().mode()[0] == (2, 3)


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
def test_versus_any_gt(order):
    assert Pool([1, 2, 3]).versus_any('>', [2, 3]).expand().mode()[0] == (3, )


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
def test_versus_any_le(order):
    assert Pool([1, 2, 3]).versus_any('<=',
                                      [1, 2]).expand().mode()[0] == (1, 2)


@pytest.mark.parametrize('order', [Order.Ascending, Order.Descending])
def test_versus_any_lt(order):
    assert Pool([1, 2, 3]).versus_any('<', [1, 2]).expand().mode()[0] == (1, )
