import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, Order
from icepool.generator.pop_order import PopOrderReason, merge_pop_orders


def test_pop_order_empty():
    assert merge_pop_orders() == (Order.Any, PopOrderReason.NoPreference)


def test_pop_order_single():
    assert merge_pop_orders(
        (Order.Ascending,
         PopOrderReason.KeepSkip)) == (Order.Ascending,
                                       PopOrderReason.KeepSkip)


def test_pop_order_priority():
    assert merge_pop_orders(
        (Order.Ascending, PopOrderReason.KeepSkip),
        (Order.Descending,
         PopOrderReason.PoolComposition)) == (Order.Descending,
                                              PopOrderReason.PoolComposition)


def test_pop_order_any():
    assert merge_pop_orders(
        (Order.Any, PopOrderReason.PoolComposition),
        (Order.Descending,
         PopOrderReason.PoolComposition)) == (Order.Descending,
                                              PopOrderReason.PoolComposition)


def test_pop_order_conflict():
    assert merge_pop_orders(
        (Order.Ascending, PopOrderReason.PoolComposition),
        (Order.Descending,
         PopOrderReason.PoolComposition)) == (None,
                                              PopOrderReason.PoolComposition)


def test_pop_order_conflict_override():
    assert merge_pop_orders(
        (Order.Ascending, PopOrderReason.KeepSkip),
        (Order.Descending, PopOrderReason.KeepSkip),
        (Order.Descending,
         PopOrderReason.PoolComposition)) == (Order.Descending,
                                              PopOrderReason.PoolComposition)


def test_pool_single_type():
    pool = icepool.Pool([d6, d6, d6])
    assert pool._local_preferred_pop_order() == (Order.Any,
                                                 PopOrderReason.NoPreference)


def test_pool_standard():
    pool = icepool.Pool([d8, d12, d6])
    assert pool._local_preferred_pop_order() == (
        Order.Descending, PopOrderReason.PoolComposition)


def test_pool_standard_negative():
    pool = icepool.Pool([-d8, -d12, -d6])
    assert pool._local_preferred_pop_order() == (
        Order.Ascending, PopOrderReason.PoolComposition)


def test_pool_non_truncate():
    pool = icepool.Pool([-d8, d12, -d6])
    assert pool._local_preferred_pop_order() == (Order.Any,
                                                 PopOrderReason.NoPreference)


def test_pool_skip_min():
    pool = icepool.Pool([d6, d6, d6])[0, 1, 1]
    assert pool._local_preferred_pop_order() == (Order.Descending,
                                                 PopOrderReason.KeepSkip)


def test_pool_skip_max():
    pool = icepool.Pool([d6, d6, d6])[1, 1, 0]
    assert pool._local_preferred_pop_order() == (Order.Ascending,
                                                 PopOrderReason.KeepSkip)


def test_pool_skip_min_but_truncate():
    pool = icepool.Pool([-d6, -d6, -d8])[0, 1, 1]
    assert pool._local_preferred_pop_order() == (
        Order.Ascending, PopOrderReason.PoolComposition)


def test_pool_skip_max_but_truncate():
    pool = icepool.Pool([d6, d6, d8])[1, 1, 0]
    assert pool._local_preferred_pop_order() == (
        Order.Descending, PopOrderReason.PoolComposition)


def test_deck_skip_min():
    deck = icepool.Deck(range(10)).deal(4)[..., 1, 1]
    assert deck._local_preferred_pop_order() == (Order.Descending,
                                                 PopOrderReason.KeepSkip)


def test_deck_skip_max():
    deck = icepool.Deck(range(10)).deal(4)[1, 1, ...]
    assert deck._local_preferred_pop_order() == (Order.Ascending,
                                                 PopOrderReason.KeepSkip)
