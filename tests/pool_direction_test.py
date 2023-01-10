import icepool
import icepool.evaluator
import pytest

from icepool import d4, d6, d8, d10, d12, Pool


class VerifyOrder(icepool.MultisetEvaluator):

    def __init__(self, order):
        self._order = order

    def next_state(self, state, outcome, count):
        if state is not None:
            if (self._order > 0) != (outcome > state):
                raise ValueError('Saw outcomes in wrong order.')
        return outcome

    def order(self, *pools):
        return self._order


verify_pos = VerifyOrder(1)
verify_neg = VerifyOrder(-1)

pool_pos = Pool([d12, d10, d8, d8, d6, d6, d6])
pool_neg = Pool([-d12, -d10, -d8, -d8, -d6, -d6, -d6])


@pytest.mark.parametrize('eval_pool', [verify_pos, verify_neg])
@pytest.mark.parametrize('pool', [pool_pos, pool_neg])
def test_order(eval_pool, pool):
    eval_pool(pool)


# The auto order should maximize skips if numerous enough.
def test_auto_order_uniform():
    algorithm, order = icepool.evaluator.sum_evaluator._select_algorithm(
        icepool.d6.pool([0, 0, 1, 1]))
    assert order > 0
    algorithm, order = icepool.evaluator.sum_evaluator._select_algorithm(
        icepool.d6.pool([1, 1, 0, 0]))
    assert order < 0


# Above that, the auto order should favor the wide-to-narrow ordering.
def test_auto_order_max_truncate_min():
    algorithm, order = icepool.evaluator.sum_evaluator._select_algorithm(
        Pool([d8, d6, d6, d6])[1, 1, 1, 0])
    assert order > 0
    algorithm, order = icepool.evaluator.sum_evaluator._select_algorithm(
        Pool([d8, d6, d6, d6])[0, 1, 1, 1])
    assert order > 0
