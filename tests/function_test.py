import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, d20, min_outcome, max_outcome, pointwise_max, pointwise_min


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

def test_pointwise_max():
    result = pointwise_max(3 @ d6, d20)
    for outcome in range(1, 21):
        assert result.probability('>=', outcome) == max(
            (3 @ d6).probability('>=', outcome),
            d20.probability('>=', outcome))
        
def test_pointwise_max_single_argument():
    result = pointwise_max([3 @ d6, d20])
    for outcome in range(1, 21):
        assert result.probability('>=', outcome) == max(
            (3 @ d6).probability('>=', outcome),
            d20.probability('>=', outcome))

def test_pointwise_min():
    result = pointwise_min(3 @ d6, d20)
    for outcome in range(1, 21):
        assert result.probability('<=', outcome) == max(
            (3 @ d6).probability('<=', outcome),
            d20.probability('<=', outcome))
        
def test_pointwise_min_single_argument():
    result = pointwise_min([3 @ d6, d20])
    for outcome in range(1, 21):
        assert result.probability('<=', outcome) == max(
            (3 @ d6).probability('<=', outcome),
            d20.probability('<=', outcome))
