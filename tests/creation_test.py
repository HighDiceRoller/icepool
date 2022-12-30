import icepool
import pytest

from icepool import Die, Deck, d6


def test_d_syntax():
    assert icepool.d6.quantities() == (1,) * 6
    assert icepool.d6.probability(0) == 0.0
    assert icepool.d6.probability(1) == pytest.approx(1.0 / 6.0)
    assert icepool.d6.probability(6) == pytest.approx(1.0 / 6.0)
    assert icepool.d6.probability(7) == 0.0


def test_coin():
    b = icepool.coin(1, 2)
    c = icepool.coin(1, 2)

    assert b.probabilities() == pytest.approx([0.5, 0.5])
    assert c.probabilities() == pytest.approx([0.5, 0.5])


def test_list_no_min_outcome():
    result = icepool.Die([2, 3, 3, 4, 4, 4, 5, 5, 6])
    expected = 2 @ icepool.d3
    assert result.equals(expected)


def test_zero_outcomes():
    die = icepool.Die(range(7), times=[0, 1, 1, 1, 1, 1, 1])
    other = icepool.d6
    assert die.has_zero_quantities()
    assert not die.equals(other)


def test_d6s():
    d6 = icepool.d6
    assert d6.equals(icepool.d(6))
    assert d6.equals(icepool.Die([d6]))
    assert d6.equals(icepool.Die([icepool.d3, icepool.d3 + 3]))
    assert d6.equals(icepool.Die({1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}))
    assert d6.equals(icepool.Die([1, 2, 3, 4, 5, 6]))


def test_return_self():
    die = icepool.d6
    assert icepool.Die(die) is die
    assert icepool.Die([die]) is die


def test_negative_weight_error():
    with pytest.raises(ValueError):
        icepool.Die({1: -1})

    with pytest.raises(ValueError):
        icepool.Die([1], times=[-1])


def test_implicit_mapping_error():
    with pytest.raises(TypeError):
        icepool.d6 + {}


def test_unsortable_error():
    with pytest.raises(TypeError):
        icepool.Die([(d6, d6)])


def test_unsortable_error_deck():
    with pytest.raises(TypeError):
        icepool.Deck([(d6, d6)])


def test_empty_tuple():
    result = icepool.Die([()])
    assert result.equals(result + ())


def test_denominator():
    result = icepool.Die([icepool.d(3), icepool.d(4), icepool.d(6)])
    assert result.denominator() == 36
