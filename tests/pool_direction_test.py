import icepool
import icepool.evaluator
import pytest

from icepool import d4, d6, d8, d10, d12, Pool, Order, UnsupportedOrder, ConflictingOrderError
import icepool.evaluator.multiset_evaluator


def test_force_order_conflict():
    with pytest.raises(ConflictingOrderError):
        d6.pool(1).force_order(Order.Ascending).force_order(
            Order.Descending).sum()


class LastOutcome(icepool.MultisetEvaluator):

    def next_state(self, state, order, outcome, count):
        return outcome


def test_order_ascending():
    assert LastOutcome().evaluate(d6.pool(1).force_order(
        Order.Ascending)).probability(6) == 1


def test_order_descending():
    assert LastOutcome().evaluate(d6.pool(1).force_order(
        Order.Descending)).probability(1) == 1


# The auto order should maximize skips if there are no other considerations.
# Note that this is the *opposite* of the preferred pop order.
def test_auto_order_uniform():
    assert LastOutcome().evaluate(d6.pool([0, 0, 1, 1])).probability(6) == 1
    assert LastOutcome().evaluate(d6.pool([1, 1, 0, 0])).probability(1) == 1


# Above that, the auto order should favor the wide-to-narrow ordering.
def test_auto_order_max_truncate_min():
    assert LastOutcome().evaluate(Pool([d8, d6, d6,
                                        d6])[1, 1, 1, 0]).probability(8) == 1
    assert LastOutcome().evaluate(Pool([d8, d6, d6,
                                        d6])[0, 1, 1, 1]).probability(8) == 1
