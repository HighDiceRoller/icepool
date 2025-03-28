import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, Order
from icepool.order import ConflictingOrderError, OrderReason, merge_order_preferences


def test_order_empty():
    assert merge_order_preferences() == (Order.Any, OrderReason.NoPreference)


def test_order_single():
    assert merge_order_preferences(
        (Order.Ascending, OrderReason.KeepSkip)) == (Order.Ascending,
                                                     OrderReason.KeepSkip)


def test_order_priority():
    assert merge_order_preferences(
        (Order.Ascending, OrderReason.KeepSkip),
        (Order.Descending,
         OrderReason.PoolComposition)) == (Order.Descending,
                                           OrderReason.PoolComposition)


def test_order_any():
    assert merge_order_preferences(
        (Order.Any, OrderReason.PoolComposition),
        (Order.Descending,
         OrderReason.PoolComposition)) == (Order.Descending,
                                           OrderReason.PoolComposition)


def test_order_conflict():
    order, order_reason = merge_order_preferences(
        (Order.Ascending, OrderReason.PoolComposition),
        (Order.Descending, OrderReason.PoolComposition))
    assert order == Order.Any
    assert order_reason > OrderReason.PoolComposition


def test_order_conflict_mandatory():
    with pytest.raises(ConflictingOrderError):
        order, order_reason = merge_order_preferences(
            (Order.Ascending, OrderReason.Mandatory),
            (Order.Descending, OrderReason.Mandatory))


def test_order_conflict_override():
    assert merge_order_preferences(
        (Order.Ascending, OrderReason.KeepSkip),
        (Order.Descending, OrderReason.KeepSkip),
        (Order.Descending,
         OrderReason.PoolComposition)) == (Order.Descending,
                                           OrderReason.PoolComposition)


def test_pool_single_type():
    pool = icepool.Pool([d6, d6, d6])
    assert pool._make_source().order_preference() == (Order.Any,
                                                      OrderReason.NoPreference)


def test_pool_standard():
    pool = icepool.Pool([d8, d12, d6])
    assert pool._make_source().order_preference() == (
        Order.Descending, OrderReason.PoolComposition)


def test_pool_standard_negative():
    pool = icepool.Pool([-d8, -d12, -d6])
    assert pool._make_source().order_preference() == (
        Order.Ascending, OrderReason.PoolComposition)


def test_pool_non_truncate():
    pool = icepool.Pool([-d8, d12, -d6])
    assert pool._make_source().order_preference() == (Order.Any,
                                                      OrderReason.NoPreference)


def test_pool_skip_min():
    pool = icepool.Pool([d6, d6, d6])[0, 1, 1]
    assert pool._make_source().order_preference() == (Order.Descending,
                                                      OrderReason.KeepSkip)


def test_pool_skip_max():
    pool = icepool.Pool([d6, d6, d6])[1, 1, 0]
    assert pool._make_source().order_preference() == (Order.Ascending,
                                                      OrderReason.KeepSkip)


def test_pool_skip_min_but_truncate():
    pool = icepool.Pool([-d6, -d6, -d8])[0, 1, 1]
    assert pool._make_source().order_preference() == (
        Order.Ascending, OrderReason.PoolComposition)


def test_pool_skip_max_but_truncate():
    pool = icepool.Pool([d6, d6, d8])[1, 1, 0]
    assert pool._make_source().order_preference() == (
        Order.Descending, OrderReason.PoolComposition)


def test_deck_skip_min():
    deck = icepool.Deck(range(10)).deal(4)[..., 1, 1]
    assert deck._make_source().order_preference() == (Order.Descending,
                                                      OrderReason.KeepSkip)


def test_deck_skip_max():
    deck = icepool.Deck(range(10)).deal(4)[1, 1, ...]
    assert deck._make_source().order_preference() == (Order.Ascending,
                                                      OrderReason.KeepSkip)
