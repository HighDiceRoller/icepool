import icepool
import pytest

from icepool import multiset_function, d6, MultisetExpression
from icepool.expand import tupleize


def test_single_expression():

    @multiset_function
    def evaluator(a):
        return a.sum()

    assert evaluator(d6.pool(3)) == 3 @ d6


def test_body_generator():

    @multiset_function
    def evaluator(a):
        return (a + d6.pool(2)).sum()

    assert evaluator(d6.pool(1)) == 3 @ d6


def test_var_args():

    @multiset_function
    def evaluator(*pools):
        return sum(pools, start=[]).sum()

    assert evaluator(d6.pool(1), d6.pool(1), d6.pool(1)) == 3 @ d6


def test_kwargs():

    @multiset_function
    def evaluator(x, target):
        return x.keep_outcomes([target]).size()

    for i in range(1, 7):
        assert evaluator(d6.pool(1), target=i) == (d6 == 1)


def test_constant():

    @multiset_function
    def evaluator(x):
        return d6.pool(3).sum()

    assert evaluator(d6.pool(1)).equals(3 @ d6, simplify=True)


def test_constant_in_joint():

    @multiset_function
    def evaluator(x):
        return d6.pool(3).sum(), x.sum()

    result = evaluator(d6.pool(2))
    expected = tupleize(3 @ d6, 2 @ d6)

    assert result.equals(expected, simplify=True)
