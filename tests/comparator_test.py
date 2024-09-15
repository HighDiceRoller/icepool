import icepool
import pytest

from icepool import d4, d6


def test_lt():
    result = icepool.d6 < icepool.d6
    expected = icepool.coin(15, 36)
    assert result.equals(expected)


def test_lt_fixed():
    assert (icepool.d6 < 1).mean() == 0
    assert (icepool.d6 < 7).mean() == 1


def test_lt_len():
    assert len(icepool.d6 < 1) == 1
    assert len(icepool.d6 < 7) == 1


def test_gt():
    result = icepool.d6 > icepool.d6
    expected = icepool.coin(15, 36)
    assert result.equals(expected)


def test_gt_fixed():
    assert (icepool.d6 > 0).mean() == 1
    assert (icepool.d6 > 6).mean() == 0


def test_gt_len():
    assert len(icepool.d6 > 0) == 1
    assert len(icepool.d6 > 6) == 1


def test_leq():
    result = icepool.d6 <= icepool.d6
    expected = icepool.coin(21, 36)
    assert result.equals(expected)


def test_leq_fixed():
    assert (icepool.d6 <= 0).mean() == 0
    assert (icepool.d6 <= 6).mean() == 1


def test_leq_len():
    assert len(icepool.d6 <= 0) == 1
    assert len(icepool.d6 <= 6) == 1


def test_geq():
    result = icepool.d6 >= icepool.d6
    expected = icepool.coin(21, 36)
    assert result.equals(expected)


def test_geq_fixed():
    assert (icepool.d6 >= 1).mean() == 1
    assert (icepool.d6 >= 7).mean() == 0


def test_geq_len():
    assert len(icepool.d6 >= 1) == 1
    assert len(icepool.d6 >= 7) == 1


def test_eq():
    result = icepool.d6 == icepool.d6
    expected = icepool.coin(6, 36)
    assert result.equals(expected)


def test_eq_fixed():
    assert (icepool.d6 == 1).equals(icepool.coin(1, 6))
    assert (icepool.d6 == 6).equals(icepool.coin(1, 6))


def test_ne():
    result = icepool.d6 != icepool.d6
    expected = icepool.coin(30, 36)
    assert result.equals(expected)


def test_ne_fixed():
    assert (icepool.d6 != 1).equals(icepool.coin(5, 6))
    assert (icepool.d6 != 6).equals(icepool.coin(5, 6))


def test_sign():
    result = (icepool.d6 - 3).sign()
    expected = icepool.Die({-1: 2, 0: 1, 1: 3})
    assert result.equals(expected)


def test_cmp():
    result = icepool.d6.cmp(icepool.d6 - 1)
    expected = icepool.Die({-1: 10, 0: 5, 1: 21})
    assert result.equals(expected)


def test_cmp_len():
    assert len(icepool.d6.cmp(0)) == 1
    assert len(icepool.d6.cmp(7)) == 1
    assert len(icepool.Die([1]).cmp(1)) == 1
    assert len(icepool.Die({-1: 0, 0: 0, 1: 0}).cmp(0)) == 0


def test_quantity_le():
    assert icepool.d6.quantity('<=', 3) == 3


def test_quantity_lt():
    assert icepool.d6.quantity('<', 3) == 2


def test_quantity_le_min():
    assert icepool.d6.quantity('<=', 1) == 1


def test_quantity_lt_min():
    assert icepool.d6.quantity('<', 1) == 0


def test_quantity_ge():
    assert icepool.d6.quantity('>=', 3) == 4


def test_quantity_gt():
    assert icepool.d6.quantity('>', 3) == 3


def test_quantity_ge_max():
    assert icepool.d6.quantity('>=', 6) == 1


def test_quantity_gt_max():
    assert icepool.d6.quantity('>', 6) == 0


die_spaced = icepool.Die(range(-3, 4), times=[1, 0, 0, 1, 0, 0, 1])


def test_quantity_le_zero_weight():
    assert die_spaced.quantity('<=', -1) == 1
    assert die_spaced.quantity('<=', 0) == 2
    assert die_spaced.quantity('<=', 1) == 2


def test_quantity_lt_zero_weight():
    assert die_spaced.quantity('<', -1) == 1
    assert die_spaced.quantity('<', 0) == 1
    assert die_spaced.quantity('<', 1) == 2


def test_quantity_ge_zero_weight():
    assert die_spaced.quantity('>=', -1) == 2
    assert die_spaced.quantity('>=', 0) == 2
    assert die_spaced.quantity('>=', 1) == 1


def test_quantity_gt_zero_weight():
    assert die_spaced.quantity('>', -1) == 2
    assert die_spaced.quantity('>', 0) == 1
    assert die_spaced.quantity('>', 1) == 1


def test_nearest_le():
    assert icepool.d6.nearest('<=', 0) == None
    assert icepool.d6.nearest('<=', 1) == 1
    assert icepool.d6.nearest('<=', 6) == 6
    assert icepool.d6.nearest('<=', 7) == 6


def test_nearest_le_gap():
    die = icepool.Die([-3, 0, 3])
    assert die.nearest('<=', -4) == None
    assert die.nearest('<=', -3) == -3
    assert die.nearest('<=', -2) == -3
    assert die.nearest('<=', -1) == -3
    assert die.nearest('<=', 0) == 0
    assert die.nearest('<=', 1) == 0
    assert die.nearest('<=', 2) == 0
    assert die.nearest('<=', 3) == 3
    assert die.nearest('<=', 4) == 3


def test_nearest_lt():
    assert icepool.d6.nearest('<', 0) == None
    assert icepool.d6.nearest('<', 1) == None
    assert icepool.d6.nearest('<', 6) == 5
    assert icepool.d6.nearest('<', 7) == 6


def test_nearest_lt_gap():
    die = icepool.Die([-3, 0, 3])
    assert die.nearest('<', -4) == None
    assert die.nearest('<', -3) == None
    assert die.nearest('<', -2) == -3
    assert die.nearest('<', -1) == -3
    assert die.nearest('<', 0) == -3
    assert die.nearest('<', 1) == 0
    assert die.nearest('<', 2) == 0
    assert die.nearest('<', 3) == 0
    assert die.nearest('<', 4) == 3


def test_nearest_ge():
    assert icepool.d6.nearest('>=', 0) == 1
    assert icepool.d6.nearest('>=', 1) == 1
    assert icepool.d6.nearest('>=', 6) == 6
    assert icepool.d6.nearest('>=', 7) == None


def test_nearest_ge_gap():
    die = icepool.Die([-3, 0, 3])
    assert die.nearest('>=', -4) == -3
    assert die.nearest('>=', -3) == -3
    assert die.nearest('>=', -2) == 0
    assert die.nearest('>=', -1) == 0
    assert die.nearest('>=', 0) == 0
    assert die.nearest('>=', 1) == 3
    assert die.nearest('>=', 2) == 3
    assert die.nearest('>=', 3) == 3
    assert die.nearest('>=', 4) == None


def test_nearest_gt():
    assert icepool.d6.nearest('>', 0) == 1
    assert icepool.d6.nearest('>', 1) == 2
    assert icepool.d6.nearest('>', 6) == None
    assert icepool.d6.nearest('>', 7) == None


def test_nearest_gt_gap():
    die = icepool.Die([-3, 0, 3])
    assert die.nearest('>', -4) == -3
    assert die.nearest('>', -3) == 0
    assert die.nearest('>', -2) == 0
    assert die.nearest('>', -1) == 0
    assert die.nearest('>', 0) == 3
    assert die.nearest('>', 1) == 3
    assert die.nearest('>', 2) == 3
    assert die.nearest('>', 3) == None
    assert die.nearest('>', 4) == None


def test_highest():
    result = icepool.highest(icepool.d4 + 1, icepool.d6)
    expected = icepool.Die({2: 2, 3: 4, 4: 6, 5: 8, 6: 4})
    assert result.equals(expected)


def test_lowest():
    result = icepool.lowest(icepool.d4 + 1, icepool.d6)
    expected = icepool.Die({1: 4, 2: 8, 3: 6, 4: 4, 5: 2})
    assert result.equals(expected)


def test_probabilities():
    assert list(d4.probabilities()) == [0.25, 0.25, 0.25, 0.25]
    assert list(d4.probabilities('<=', )) == [0.25, 0.5, 0.75, 1.0]
    assert list(d4.probabilities('<', )) == [0.0, 0.25, 0.5, 0.75]
    assert list(d4.probabilities('>=', )) == [1.0, 0.75, 0.5, 0.25]
    assert list(d4.probabilities('>', )) == [0.75, 0.5, 0.25, 0.0]

    assert list(d4.probabilities(percent=True)) == [25, 25, 25, 25]
    assert list(d4.probabilities('<=', percent=True)) == [25, 50, 75, 100]
    assert list(d4.probabilities('<', percent=True)) == [0, 25, 50, 75]
    assert list(d4.probabilities('>=', percent=True)) == [100, 75, 50, 25]
    assert list(d4.probabilities('>', percent=True)) == [75, 50, 25, 0]


def test_probabilities_with_target():
    pytest.skip('target is no longer supported')
    target = [1, 4, 5]
    assert list(d4.probabilities(target)) == [0.25, 0.25, 0.0]
    assert list(d4.probabilities('<=', target)) == [0.25, 1.0, 1.0]
    assert list(d4.probabilities('<', target)) == [0.0, 0.75, 1.0]
    assert list(d4.probabilities('>=', target)) == [1.0, 0.25, 0.0]
    assert list(d4.probabilities('>', target)) == [0.75, 0.0, 0.0]
