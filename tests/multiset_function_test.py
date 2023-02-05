import icepool
import pytest

from icepool import multiset_function, d6, cartesian_product, MultisetExpression


def test_single_expression():

    @multiset_function
    def evaluator(a):
        return a.sum()

    assert evaluator(d6.pool(3)) == 3 @ d6
