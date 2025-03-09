import icepool
import icepool.evaluator
import pytest

from icepool import d4, d6, d8, d10, d12, Pool
import icepool.evaluator.multiset_evaluator


class LastOutcomeAscending(icepool.MultisetEvaluator):

    def next_state_ascending(self, state, outcome, count):
        return outcome


class LastOutcomeDescending(icepool.MultisetEvaluator):

    def next_state_descending(self, state, outcome, count):
        return outcome


def test_order_ascending():
    assert LastOutcomeAscending().evaluate(d6.pool(1)).probability(6) == 1


def test_order_descending():
    assert LastOutcomeDescending().evaluate(d6.pool(1)).probability(1) == 1


fake_dungeon = icepool.evaluator.multiset_evaluator.MultisetEvaluatorDungeon(
    None, lambda: None, lambda: None, lambda: None, lambda: None, {})


class LastOutcome(icepool.MultisetEvaluator):

    def next_state(self, state, outcome, count):
        return outcome


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
