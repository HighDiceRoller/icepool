import pytest
from icepool import MultisetEvaluator, NoCache, multiset_function, d6


class CacheTestEvaluator(MultisetEvaluator):

    def next_state(self, state, order, outcome, /, *counts):
        return 0

    def final_outcome(self, final_state, order, outcomes, /, *sizes, **kwargs):
        return 0


class KeyedEvaluator(CacheTestEvaluator):

    @property
    def next_state_key(self):
        return type(self)


class KeylessEvaluator(CacheTestEvaluator):
    pass


class NoCacheEvaluator(CacheTestEvaluator):

    @property
    def next_state_key(self):
        return NoCache


def test_keyed_bare():
    evaluator = KeyedEvaluator()
    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 1
    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 1


def test_keyless_bare():
    evaluator = KeylessEvaluator()
    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 1
    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 1


def test_nocache_bare():
    evaluator = NoCacheEvaluator()
    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 0


def test_keyed_wrapped():

    @multiset_function
    def evaluator(x):
        return KeyedEvaluator().evaluate(x)

    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 1


def test_keyless_wrapped():

    @multiset_function
    def evaluator(x):
        return KeylessEvaluator().evaluate(x)

    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 0


def test_nocache_wrapped():

    @multiset_function
    def evaluator(x):
        return NoCacheEvaluator().evaluate(x)

    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 0


def test_joint_cache():

    @multiset_function
    def evaluator(x):
        return KeyedEvaluator().evaluate(x), KeyedEvaluator().evaluate(x)

    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 1
    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 1


def test_joint_nocache():

    @multiset_function
    def evaluator(x):
        return KeyedEvaluator().evaluate(x), NoCacheEvaluator().evaluate(x)

    evaluator(d6.pool(1))
    assert len(evaluator._cache) == 0
