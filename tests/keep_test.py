import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, Pool, Die, Deck, multiset_function, Order

max_tuple_length = 5
max_num_values = 5


def bf_keep_highest(die, num_dice, keep, drop=0):
    if keep == 0:
        return icepool.Die([0])

    def function(*outcomes):
        return sum(sorted(outcomes)[-(keep + drop):len(outcomes) - drop])

    return icepool.map(function, *([die] * num_dice))


def bf_keep_lowest(die, num_dice, keep, drop=0):
    if keep == 0:
        return icepool.Die([0])

    def function(*outcomes):
        return sum(sorted(outcomes)[drop:keep + drop])

    return icepool.map(function, *([die] * num_dice))


def bf_keep(die, num_dice, keep_indexes):

    def function(*outcomes):
        return sorted(outcomes)[keep_indexes]

    return icepool.map(function, *([die] * num_dice))


def bf_diff_highest_lowest(die, num_dice):

    def function(*outcomes):
        return max(outcomes) - min(outcomes)

    return icepool.map(function, *([die] * num_dice))


@pytest.mark.parametrize('keep', range(1, 6))
def test_keep_highest(keep):
    die = icepool.d12
    result = die.highest(4, keep)
    expected = bf_keep_highest(die, 4, keep)
    assert result == expected


@pytest.mark.parametrize('keep', range(1, 6))
def test_keep_highest_drop_highest(keep):
    die = icepool.d12
    result = die.highest(4, keep, drop=1)
    expected = bf_keep_highest(die, 4, keep, drop=1)
    assert result == expected


def test_keep_highest_open_bound():
    die = icepool.d12
    result = die.highest(4, drop=1)
    expected = bf_keep_highest(die, 4, keep=3, drop=1)
    assert result == expected


@pytest.mark.parametrize('keep', range(1, 6))
def test_keep_lowest(keep):
    die = icepool.d12
    result = die.lowest(4, keep)
    expected = bf_keep_lowest(die, 4, keep)
    assert result == expected


@pytest.mark.parametrize('keep', range(1, 6))
def test_keep_lowest_drop_highest(keep):
    die = icepool.d12
    result = die.lowest(4, keep, drop=1)
    expected = bf_keep_lowest(die, 4, keep, drop=1)
    assert result == expected


def test_keep_lowest_open_bound():
    die = icepool.d12
    result = die.lowest(4, drop=1)
    expected = bf_keep_lowest(die, 4, keep=3, drop=1)
    assert result == expected


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
    expected = 2 * icepool.d6.highest(5, 1, drop=2)
    assert result == expected


def test_pool_select_negative():
    pool = icepool.d6.pool(5)
    result = icepool.evaluator.sum_evaluator.evaluate(pool[0, 0, -2, 0, 0])
    expected = -2 * icepool.d6.highest(5, 1, drop=2)
    assert result == expected


def test_pool_select_mixed_sign():
    pool = icepool.d6.pool(2)
    result = icepool.evaluator.sum_evaluator.evaluate(pool[-1, 1])
    expected = abs(icepool.d6 - icepool.d6)
    assert result == expected


def test_pool_select_mixed_sign_split():
    pool = icepool.d6.pool(4)
    result = icepool.evaluator.sum_evaluator.evaluate(pool[-1, 0, 0, 1])
    expected = bf_diff_highest_lowest(icepool.d6, 4)
    assert result == expected


def test_highest():
    result = icepool.highest(icepool.d6, icepool.d6)
    expected = icepool.d6.highest(2, 1)
    assert result == expected


def test_lowest():
    result = icepool.lowest(icepool.d6, icepool.d6)
    expected = icepool.d6.lowest(2, 1)
    assert result == expected


def test_double_index():
    result = d6.pool(3)[:2][-1]
    expected = d6.pool(3)[1]
    assert result == expected


def test_expression_keep():
    result = (d6.pool(3) | d6.pool(3))[0]
    expected = d6.pool(6)[0]
    assert result == expected


def test_bad_pool_keep_int():
    with pytest.raises(IndexError):
        d6.pool(3)[10]


def test_bad_expression_keep_int():
    with pytest.raises(IndexError):
        (d6.pool(3) & d6.pool(3))[0]


def test_middle_odd():
    result = Pool([0, 10, 20]).middle(1).sum()
    expected = Die([10])
    assert result == expected


def test_middle_even():
    result = Pool([0, 10, 20, 30]).middle(2).sum()
    expected = Die([30])
    assert result == expected


def test_middle_odd_index_even_pool_error():
    with pytest.raises(IndexError):
        Pool([0, 10, 20, 30]).middle(3).sum()


def test_middle_odd_index_even_pool_low():
    result = Pool([0, 10, 20, 30]).middle(3, tie='low').sum()
    expected = Die([30])
    assert result == expected


def test_middle_odd_index_even_pool_high():
    result = Pool([0, 10, 20, 30]).middle(3, tie='high').sum()
    expected = Die([60])
    assert result == expected


def test_middle_even_index_odd_pool_error():
    with pytest.raises(IndexError):
        Pool([0, 10, 20, 30, 40]).middle(2).sum()


def test_middle_even_index_odd_pool_low():
    result = Pool([0, 10, 20, 30, 40]).middle(2, tie='low').sum()
    expected = Die([30])
    assert result == expected


def test_middle_even_index_odd_pool_high():
    result = Pool([0, 10, 20, 30, 40]).middle(2, tie='high').sum()
    expected = Die([50])
    assert result == expected


def test_keep_expression_near_nonnegative():
    result = Deck([0, 10, 20, 30, 40]).deal(5)[:2].sum()
    expected = Die([10])
    assert result == expected


def test_keep_expression_far_nonnegative():
    result = Deck([0, 10, 20, 30, 40]).deal(5)[2:].sum()
    expected = Die([90])
    assert result == expected


def test_keep_expression_near_negative():
    result = Deck([0, 10, 20, 30, 40]).deal(5)[-2:].sum()
    expected = Die([70])
    assert result == expected


def test_keep_expression_far_negative():
    result = Deck([0, 10, 20, 30, 40]).deal(5)[:-2].sum()
    expected = Die([30])
    assert result == expected


def test_keep_expression_both_nonnegative():
    result = Deck([0, 10, 20, 30, 40]).deal(5)[1:4].sum()
    expected = Die([60])
    assert result == expected


def test_keep_expression_both_negative():
    result = Deck([0, 10, 20, 30, 40]).deal(5)[-4:-1].sum()
    expected = Die([60])
    assert result == expected


def test_keep_expression_positive_negative():
    result = Deck([0, 10, 20, 30, 40]).deal(5)[1:-1].sum()
    expected = Die([60])
    assert result == expected


def test_keep_expression_negative_positive():
    result = Deck([0, 10, 20, 30, 40]).deal(5)[-4:4].sum()
    expected = Die([60])
    assert result == expected


def test_keep_die_method():
    assert d6.keep((0, 1, 0)) == d6.pool(3).keep(1)
    assert d6.keep(3, 1) == d6.pool(3).keep(1)
    assert d6.keep(5, (1, ...)) == d6.lowest(5, 1)


def test_keep_drop_negative_counts():
    assert (d6.pool(3) - d6.pool(3)).highest(1).sum() == (
        +(d6.pool(3) - d6.pool(3))).highest(1).sum()


def test_keep_negative_fallback():
    assert d6.pool(2)[-1, 1].highest(1).sum() == Die({
        0: 6,
        2: 2,
        3: 4,
        4: 6,
        5: 8,
        6: 10
    })


def test_keep_known_size_ascending():

    @multiset_function
    def test(x):
        return x.force_order(Order.Ascending)[-1]

    assert test(d6.pool(3)) == d6.highest(3)


def test_keep_known_size_descending():

    @multiset_function
    def test(x):
        return x.force_order(Order.Descending)[0]

    assert test(d6.pool(3)) == d6.lowest(3)
