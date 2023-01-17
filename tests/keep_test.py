import icepool
import pytest

from icepool import d4, d6, d8, d10, d12

max_tuple_length = 5
max_num_values = 5


def bf_keep_highest(die, num_dice, keep, drop=0):
    if keep == 0:
        return icepool.Die([0])

    def func(*outcomes):
        return sum(sorted(outcomes)[-(keep + drop):len(outcomes) - drop])

    return icepool.apply(func, *([die] * num_dice))


def bf_keep_lowest(die, num_dice, keep, drop=0):
    if keep == 0:
        return icepool.Die([0])

    def func(*outcomes):
        return sum(sorted(outcomes)[drop:keep + drop])

    return icepool.apply(func, *([die] * num_dice))


def bf_keep(die, num_dice, keep_indexes):

    def func(*outcomes):
        return sorted(outcomes)[keep_indexes]

    return icepool.apply(func, *([die] * num_dice))


def bf_diff_highest_lowest(die, num_dice):

    def func(*outcomes):
        return max(outcomes) - min(outcomes)

    return icepool.apply(func, *([die] * num_dice))


@pytest.mark.parametrize('keep', range(1, 6))
def test_keep_highest(keep):
    die = icepool.d12
    result = die.sum_highest(4, keep)
    expected = bf_keep_highest(die, 4, keep)
    assert result.equals(expected)


@pytest.mark.parametrize('keep', range(1, 6))
def test_keep_highest_zero_weights(keep):
    die = icepool.Die(range(6), times=[0, 0, 1, 1, 1, 1])
    result = die.sum_highest(4, keep).trim()
    expected = bf_keep_highest(icepool.d4 + 1, 4, keep)
    assert result.equals(expected)


@pytest.mark.parametrize('keep', range(1, 6))
def test_keep_highest_drop_highest(keep):
    die = icepool.d12
    result = die.sum_highest(4, keep, drop=1)
    expected = bf_keep_highest(die, 4, keep, drop=1)
    assert result.equals(expected)


@pytest.mark.parametrize('keep', range(1, 6))
def test_keep_lowest(keep):
    die = icepool.d12
    result = die.sum_lowest(4, keep)
    expected = bf_keep_lowest(die, 4, keep)
    assert result.equals(expected)


@pytest.mark.parametrize('keep', range(1, 6))
def test_keep_lowest_drop_highest(keep):
    die = icepool.d12
    result = die.sum_lowest(4, keep, drop=1)
    expected = bf_keep_lowest(die, 4, keep, drop=1)
    assert result.equals(expected)


def test_pool_select():
    pool = icepool.Pool([icepool.d6] * 5)
    assert pool[-2] == pool[-2:-1].sum()
    assert pool[-2:].keep_tuple() == (0, 0, 0, 1, 1)


def test_sum_from_pool():
    pool = icepool.Pool([icepool.d6] * 5)
    assert pool.sum().equals(5 @ icepool.d6)


def test_pool_select_multi():
    pool = icepool.d6.pool(5)
    result = icepool.evaluator.sum_evaluator.evaluate(pool[0, 0, 2, 0, 0])
    expected = 2 * icepool.d6.sum_highest(5, 1, drop=2)
    assert result.equals(expected)


def test_pool_select_negative():
    pool = icepool.d6.pool(5)
    result = icepool.evaluator.sum_evaluator.evaluate(pool[0, 0, -2, 0, 0])
    expected = -2 * icepool.d6.sum_highest(5, 1, drop=2)
    assert result.equals(expected)


def test_pool_select_mixed_sign():
    pool = icepool.d6.pool(2)
    result = icepool.evaluator.sum_evaluator.evaluate(pool[-1, 1])
    expected = abs(icepool.d6 - icepool.d6)
    assert result.equals(expected)


def test_pool_select_mixed_sign_split():
    pool = icepool.d6.pool(4)
    result = icepool.evaluator.sum_evaluator.evaluate(pool[-1, 0, 0, 1])
    expected = bf_diff_highest_lowest(icepool.d6, 4)
    assert result.equals(expected)


def test_highest():
    result = icepool.sum_highest(icepool.d6, icepool.d6)
    expected = icepool.d6.sum_highest(2, 1)
    assert result.equals(expected)


def test_lowest():
    result = icepool.sum_lowest(icepool.d6, icepool.d6)
    expected = icepool.d6.sum_lowest(2, 1)
    assert result.equals(expected)


def test_double_index():
    result = d6.pool(3)[:2][-1]
    expected = d6.pool(3)[1]
    assert result == expected
