import icepool
import icepool.evaluator
import pytest

from icepool import d4, d6, d8, d10, d12, Pool


class VerifyOrderAscending(icepool.MultisetEvaluator):

    def next_state_ascending(self, state, outcome, count):
        return outcome


class VerifyOrderDescending(icepool.MultisetEvaluator):

    def next_state_descending(self, state, outcome, count):
        return outcome


def test_order_ascending():
    assert VerifyOrderAscending().evaluate(d6.pool(1)).probability(6) == 1


def test_order_descending():
    assert VerifyOrderDescending().evaluate(d6.pool(1)).probability(1) == 1


# The auto order should maximize skips if there are no other considerations.
# Note that this is the *opposite* of the preferred pop order.
def test_auto_order_uniform():
    inputs = (d6.pool([0, 0, 1, 1]), )
    input_order, eval_order = icepool.evaluator.sum_evaluator._prepare(
        inputs, {})[0]._select_order(inputs)
    assert input_order < 0
    assert eval_order > 0
    inputs = (d6.pool([1, 1, 0, 0]), )
    input_order, eval_order = icepool.evaluator.sum_evaluator._prepare(
        inputs, {})[0]._select_order(inputs)
    assert input_order > 0
    assert eval_order < 0


# Above that, the auto order should favor the wide-to-narrow ordering.
def test_auto_order_max_truncate_min():
    inputs = (Pool([d8, d6, d6, d6])[1, 1, 1, 0], )
    input_order, eval_order = icepool.evaluator.sum_evaluator._prepare(
        inputs, {})[0]._select_order(inputs)
    assert input_order < 0
    assert eval_order > 0
    inputs = (Pool([d8, d6, d6, d6])[0, 1, 1, 1], )
    input_order, eval_order = icepool.evaluator.sum_evaluator._prepare(
        inputs, {})[0]._select_order(inputs)
    assert input_order < 0
    assert eval_order > 0
