import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, Pool


class VerifyDirection(icepool.OutcomeCountEvaluator):

    def __init__(self, direction):
        self._direction = direction

    def next_state(self, state, outcome, count):
        if state is not None:
            if (self._direction > 0) != (outcome > state):
                raise ValueError('Saw outcomes in wrong direction.')
        return outcome

    def direction(self, *pools):
        return self._direction


verify_pos = VerifyDirection(1)
verify_neg = VerifyDirection(-1)

pool_pos = Pool([d12, d10, d8, d8, d6, d6, d6])
pool_neg = Pool([-d12, -d10, -d8, -d8, -d6, -d6, -d6])


@pytest.mark.parametrize('eval_pool', [verify_pos, verify_neg])
@pytest.mark.parametrize('pool', [pool_pos, pool_neg])
def test_direction(eval_pool, pool):
    eval_pool(pool)


# The auto direction should maximize skips if numerous enough.
def test_auto_direction_uniform():
    algorithm, direction = icepool.evaluate_sum._select_algorithm(
        icepool.d6.pool()[0, 0, 1, 1])
    assert direction > 0
    algorithm, direction = icepool.evaluate_sum._select_algorithm(
        icepool.d6.pool()[1, 1, 0, 0])
    assert direction < 0


# Above that, the auto direction should favor the wide-to-narrow ordering.
def test_auto_direction_max_truncate_min():
    algorithm, direction = icepool.evaluate_sum._select_algorithm(
        Pool([d8, d6, d6, d6])[1, 1, 1, 0])
    assert direction > 0
    algorithm, direction = icepool.evaluate_sum._select_algorithm(
        Pool([d8, d6, d6, d6])[0, 1, 1, 1])
    assert direction > 0
