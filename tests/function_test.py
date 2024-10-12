import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, d20, min_outcome, max_outcome, highest_threshold, lowest_threshold


def test_min_outcome_single_arg():
    assert min_outcome([d6, d8]) == 1


def test_min_outcome_multiple_arg():
    assert min_outcome(d6, d8) == 1


def test_min_outcome_bare_outcome():
    assert min_outcome(d6, d8, 0, 2) == 0


def test_max_outcome_single_arg():
    assert max_outcome([d6, d8]) == 8


def test_max_outcome_multiple_arg():
    assert max_outcome(d6, d8) == 8


def test_max_outcome_bare_outcome():
    assert max_outcome(d6, d8, 10, 2) == 10

def test_highest_threshold():
    result = highest_threshold(3 @ d6, d20)
    for outcome in range(1, 21):
        assert result.probability('>=', outcome) == max(
            (3 @ d6).probability('>=', outcome),
            d20.probability('>=', outcome))

def test_lowest_threshold():
    result = lowest_threshold(3 @ d6, d20)
    for outcome in range(1, 21):
        assert result.probability('<=', outcome) == max(
            (3 @ d6).probability('<=', outcome),
            d20.probability('<=', outcome))
