import icepool
import pytest

from icepool import Die, d6, Deck
from fractions import Fraction


def test_d6_mean():
    assert icepool.d6.mean() == 3.5


def test_d8_variance():
    assert icepool.d8.variance() == 63 / 12


def test_kolmogorov_smirnov_standard_dice():
    assert icepool.d10.kolmogorov_smirnov(icepool.d20) == Fraction(1, 2)


def test_kolmogorov_smirnov_flat_number():
    assert icepool.Die([10]).kolmogorov_smirnov(icepool.Die([10])) == 0
    assert icepool.Die([10]).kolmogorov_smirnov(icepool.Die([9])) == 1


def test_d6_median():
    assert icepool.d6.median_low() == 3
    assert icepool.d6.median_high() == 4
    assert icepool.d6.median() == 3.5


def test_d7_median():
    assert icepool.d7.median_low() == 4
    assert icepool.d7.median_high() == 4
    assert icepool.d7.median() == 4


def test_min_quantile():
    assert icepool.d6.quantile_low(0) == 1
    assert icepool.d6.quantile_high(0) == 1


def test_max_quantile():
    assert icepool.d6.quantile_low(100) == 6
    assert icepool.d6.quantile_high(100) == 6


def test_entropy_with_zeros():
    assert Die({1: 1, 2: 0, 3: 1}).entropy() == 1.0


@pytest.mark.parametrize('comparison', ['==', '!=', '<=', '<', '>=', '>'])
def test_percent(comparison):
    die = 3 @ d6
    assert die.probability(
        comparison, 4, percent=True) == die.probability(comparison, 4) * 100.0


def test_pad_to_denominator_add():
    deck = Deck([0, 1, 2, 3]).pad_to_denominator(6, 0)
    assert deck == Deck([0, 0, 0, 1, 2, 3])


def test_pad_to_denominator_remove():
    deck = Deck([0, 0, 0, 1, 2, 3]).pad_to_denominator(4, 0)
    assert deck == Deck([0, 1, 2, 3])


def test_pad_to_denominator_zero():
    deck = Deck([0, 0, 0, 1, 2, 3]).pad_to_denominator(3, 0)
    assert deck == Deck([1, 2, 3])


def test_pad_to_denominator_negative_error():
    with pytest.raises(ValueError):
        deck = Deck([0, 0, 0, 1, 2, 3]).pad_to_denominator(2, 0)
