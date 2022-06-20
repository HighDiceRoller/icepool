import _context

import icepool
import pytest

from icepool import d4, d6, d8, d10, d12

class SumRerollIfAnyOnes(icepool.OutcomeGroupEvaluator):
    def next_state(self, state, outcome, count):
        if outcome == 1 and count > 0:
            return icepool.Reroll
        elif state is None:
            return outcome * count
        else:
            return state + outcome * count
    
    def direction(self, *_):
        return 0

def test_reroll():
    result = SumRerollIfAnyOnes().evaluate(icepool.d6.pool(5))
    expected = 5 @ (icepool.d5+1)
    assert result.equals(expected)

class SumPoolDescending(icepool.SumGenerator):
    def direction(self, pool):
        return -1

def test_sum_descending():
    result = SumPoolDescending().evaluate(icepool.d6.pool(3))
    expected = 3 @ icepool.d6
    assert result.equals(expected)

def test_sum_descending_limit_outcomes():
    result = -SumPoolDescending().evaluate((-icepool.d8, -icepool.d6))
    expected = icepool.d6 + icepool.d8
    assert result.equals(expected)

def test_sum_descending_keep_highest():
    result = SumPoolDescending().evaluate(icepool.d6.pool()[0, 1, 1, 1])
    expected = icepool.d6.keep_highest(4, 3)
    assert result.equals(expected)

def test_zero_weight_outcomes():
    result = icepool.Die(range(5), times=[0, 1, 0, 1, 0]).keep_highest(3, 2)
    assert len(result) == 9

def sum_dice_func(state, outcome, count):
    return (state or 0) + outcome * count

def test_wrap_func_evaluate():
    result = icepool.d6.pool()[0,0,1,1,1].evaluate(sum_dice_func)
    expected = icepool.d6.keep_highest(5, 3)
    assert result.equals(expected)

def test_standard_pool():
    result = icepool.standard_pool([8, 8, 6, 6, 6]).sum()
    expected = 3 @ icepool.d6 + 2 @ icepool.d8
    assert result.equals(expected)

def test_standard_pool_zero_dice():
    result = icepool.standard_pool([]).sum()
    expected = icepool.Die([0])
    assert result.equals(expected)

def test_runs():
    result = icepool.FindBestRun()(icepool.standard_pool([12, 10, 8]))
    def func(*outcomes):
        outcomes = sorted(outcomes)
        a = outcomes[1] == outcomes[0] + 1
        b = outcomes[2] == outcomes[1] + 1
        if a and b:
            return 3, outcomes[2]
        elif b:
            return 2, outcomes[2]
        elif a:
            return 2, outcomes[1]
        else:
            return 1, outcomes[2]
    expected = icepool.apply(func, icepool.d12, icepool.d10, icepool.d8)
    assert result.equals(expected)
    
def test_runs_skip():
    die = icepool.Die([0, 10])
    result = icepool.FindBestRun()(die.pool(10))
    assert result.outcomes() == ((1, 0), (1, 10))

class SumFixedDirection(icepool.OutcomeGroupEvaluator):
    def __init__(self, direction):
        self._direction = direction

    def next_state(self, state, outcome, count):
        return (state or 0) + outcome * count
    
    def direction(self, *pools):
        return self._direction

test_pools = [
    icepool.standard_pool([6,6,6]),
    icepool.standard_pool([6,6,6,6])[0,0,0,1],
    icepool.standard_pool([6,6,6,6])[0,1,1,1],
    icepool.standard_pool([6,6,6,6])[-1,0,0,1],
    icepool.standard_pool([12,10,8,8,6,6,6,4]),
    icepool.Pool([-d6, -d8, -d10]),
    (3 @ icepool.d6).pool(12)[-6:],
]

eval_ascending = SumFixedDirection(1)
eval_descending = SumFixedDirection(-1)
eval_auto = SumFixedDirection(0)

@pytest.mark.parametrize('pool', test_pools)
def test_sum_direction(pool):
    assert eval_ascending.evaluate(pool).equals(eval_descending.evaluate(pool))
    assert eval_ascending.evaluate(pool).equals(eval_auto.evaluate(pool))

def test_joint_evaluate():
    test_evaluator = icepool.JointEvaluator(icepool.sum_generator, icepool.sum_generator)
    result = test_evaluator(icepool.d6.pool(3))
    expected = (3 @ icepool.d6).sub(lambda x: (x, x))
    assert result.equals(expected)

def test_enumerate_pool_vs_cartesian_product():
    result = icepool.enumerate_generator(d6.pool(3))
    expected = icepool.Die([(d6, d6, d6)]).sub(lambda x: tuple(sorted(x)))
    assert result.equals(expected)

@pytest.mark.parametrize('pool', test_pools)
def test_enumerate_pool_vs_sum(pool):
    if any(x < 0 for x in pool.post_roll_counts()):
        with pytest.raises(ValueError):
            icepool.enumerate_generator(pool)
    else:
        result = icepool.enumerate_generator(pool).sub(sum)
        expected = pool.sum()
        assert result.equals(expected)
