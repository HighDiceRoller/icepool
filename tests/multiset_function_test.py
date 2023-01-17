import icepool
import pytest

from icepool import multiset_function, d6, cartesian_product


def test_fully_bound_expression():
    evaluator = multiset_function(lambda: d6.pool(3).sum())
    assert evaluator() == 3 @ d6


def test_fully_bound_joint_expression():
    evaluator = multiset_function(lambda a: (d6.pool(3).sum(), a.sum()))
    assert evaluator(d6.pool(2)) == cartesian_product(3 @ d6, 2 @ d6)
