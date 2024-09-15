import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, min_outcome, max_outcome


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
