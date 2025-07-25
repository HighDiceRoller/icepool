import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, Pool, Vector, Order, UnsupportedOrder
from icepool.evaluator.multiset_function import multiset_function


class SumRerollIfAnyOnes(icepool.MultisetEvaluator):

    def next_state(self, state, order, outcome, count):
        if outcome == 1 and count > 0:
            return icepool.Reroll
        elif state is None:
            return outcome * count
        else:
            return state + outcome * count


def test_reroll():
    result = SumRerollIfAnyOnes().evaluate(icepool.d6.pool(5))
    expected = 5 @ (icepool.d5 + 1)
    assert result.equals(expected)


class SumPoolDescending(icepool.evaluator.SumEvaluator):

    def order(self):
        return -1


def test_sum_descending():
    result = SumPoolDescending().evaluate(icepool.d6.pool(3))
    expected = 3 @ icepool.d6
    assert result.equals(expected)


def test_sum_descending_limit_outcomes():
    result = -SumPoolDescending().evaluate(Pool([-icepool.d8, -icepool.d6]))
    expected = icepool.d6 + icepool.d8
    assert result.equals(expected)


def test_sum_descending_keep_highest():
    result = SumPoolDescending().evaluate(icepool.d6.pool([0, 1, 1, 1]))
    expected = icepool.d6.highest(4, 3)
    assert result.equals(expected)


def test_zero_weight_outcomes():
    result = icepool.Die(range(5), times=[0, 1, 0, 1, 0]).highest(3, 2)
    assert len(result) == 3


def sum_dice_func(state, outcome, count):
    return (state or 0) + outcome * count


def test_standard_pool():
    result = icepool.standard_pool([8, 8, 6, 6, 6]).sum()
    expected = 3 @ icepool.d6 + 2 @ icepool.d8
    assert result.equals(expected)

    result_dict = icepool.standard_pool({8: 2, 6: 3}).sum()
    assert result.equals(result_dict)


def test_standard_pool_zero_dice():
    result = icepool.standard_pool([]).sum()
    expected = icepool.Die([0])
    assert result.equals(expected)


class LargestStraightAndOutcomeEvaluatorDescending(
        icepool.evaluator.LargestStraightAndOutcomeEvaluator):

    def order(self):
        return Order.Descending


def test_runs():
    pool = icepool.standard_pool([12, 10, 8])
    result = icepool.evaluator.LargestStraightAndOutcomeEvaluator('high')(pool)

    def function(*outcomes):
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

    expected = icepool.map(function, pool, star=True)
    assert result.equals(expected)

    result_descending = LargestStraightAndOutcomeEvaluatorDescending('high')(
        pool)
    assert result_descending.equals(expected)


def test_runs_low():
    pool = icepool.standard_pool([12, 10, 8])
    result = icepool.evaluator.LargestStraightAndOutcomeEvaluator('low')(
        icepool.standard_pool([12, 10, 8]))

    def function(*outcomes):
        outcomes = sorted(outcomes)
        a = outcomes[1] == outcomes[0] + 1
        b = outcomes[2] == outcomes[1] + 1
        if a and b:
            return 3, outcomes[0]
        elif a:
            return 2, outcomes[0]
        elif b:
            return 2, outcomes[1]
        else:
            return 1, outcomes[0]

    expected = icepool.map(function, pool, star=True)
    assert result.equals(expected)

    result_descending = LargestStraightAndOutcomeEvaluatorDescending('low')(
        pool)
    assert result_descending.equals(expected)


def test_runs_skip():
    die = icepool.Die([0, 10])
    result = icepool.evaluator.LargestStraightAndOutcomeEvaluator('high')(
        die.pool(10))
    assert tuple(result.outcomes()) == ((1, 0), (1, 10))


class SumFixedOrderAuto(icepool.MultisetEvaluator):

    def next_state(self, state, order, outcome, count):
        return (state or 0) + outcome * count


class SumFixedOrderAscending(icepool.MultisetEvaluator):

    def next_state(self, state, order, outcome, count):
        if order != Order.Ascending:
            raise UnsupportedOrder()
        return (state or 0) + outcome * count


class SumFixedOrderDescending(icepool.MultisetEvaluator):

    def next_state(self, state, order, outcome, count):
        if order != Order.Descending:
            raise UnsupportedOrder()
        return (state or 0) + outcome * count


test_pools = [
    icepool.standard_pool([6, 6, 6]),
    icepool.standard_pool([6, 6, 6, 6])[0, 0, 0, 1],
    icepool.standard_pool([6, 6, 6, 6])[0, 1, 1, 1],
    icepool.standard_pool([6, 6, 6, 6])[-1, 0, 0, 1],
    icepool.standard_pool([12, 10, 8, 8, 6, 6, 6, 4]),
    icepool.Pool([-d6, -d8, -d10]),
    (3 @ icepool.d6).pool(12)[-6:],
]

eval_ascending = SumFixedOrderAscending()
eval_descending = SumFixedOrderDescending()
eval_auto = SumFixedOrderAuto()


@pytest.mark.parametrize('pool', test_pools)
def test_sum_order(pool):
    assert eval_ascending.evaluate(pool).equals(eval_descending.evaluate(pool))
    assert eval_ascending.evaluate(pool).equals(eval_auto.evaluate(pool))


def test_joint_evaluate():

    @multiset_function
    def test_evaluator(x):
        return x.sum(), x.sum()

    result = test_evaluator(icepool.d6.pool(3))
    expected = (3 @ icepool.d6).map(lambda x: (x, x))
    assert result.equals(expected)


def test_joint_evaluator_order_ascending():

    @multiset_function
    def joint_evaluation(x):
        return eval_ascending(x), eval_auto(x)

    result = joint_evaluation(icepool.d6.pool(3))
    expected = (3 @ icepool.d6).map(lambda x: (x, x))
    assert result.equals(expected)


def test_joint_evaluator_order_descending():

    @multiset_function
    def joint_evaluation(x):
        return eval_descending(x), eval_auto(x)

    result = joint_evaluation(icepool.d6.pool(3))
    expected = (3 @ icepool.d6).map(lambda x: (x, x))
    assert result.equals(expected)


def test_enumerate_pool_vs_outer_product():
    result = icepool.evaluator.ExpandEvaluator()(d6.pool(3))
    expected = icepool.vectorize(d6, d6, d6).map(lambda x: tuple(sorted(x)))
    assert result.equals(expected)


@pytest.mark.parametrize('pool', test_pools)
def test_expand_vs_sum(pool):
    if any(x < 0 for x in pool.keep_tuple()):
        pytest.skip()
    else:
        result = icepool.evaluator.ExpandEvaluator()(pool).map(sum)
        expected = pool.sum()
        assert result.equals(expected)


def test_contains_subset_vs_intersection_size():
    pool = icepool.d6.pool(10)
    result_a = pool.issuperset([1, 2, 3, 3])
    result_b = (pool & [1, 2, 3, 3]).size() == 4
    assert result_a == result_b


def test_empty():
    result = (d6.pool(1) & d6.pool(1)).empty()
    assert result == (d6 != d6)
