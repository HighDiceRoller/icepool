import icepool
import pytest

from icepool import multiset_function, d6, MultisetExpression


def test_single_expression():

    @multiset_function
    def evaluator(a):
        return a.sum()

    assert evaluator(d6.pool(3)) == 3 @ d6


def test_bound_generator():

    @multiset_function
    def evaluator(a):
        return (a + d6.pool(2)).sum()

    assert evaluator(d6.pool(1)) == 3 @ d6
