import icepool
import pytest

from icepool import d4, d6, d8, d10, d12, OutcomeCountEvaluator, Pool


class CallPathLength(OutcomeCountEvaluator):

    def next_state(self, state, outcome, *pools):
        return (state or 0) + 1

    alignment = OutcomeCountEvaluator.range_alignment


call_path_length = CallPathLength()


def test_simple_pool():
    pool = d6.pool(5)
    result = call_path_length.evaluate(pool)
    assert result.outcomes() == (6,)


def test_individual_outcomes():
    pool = Pool([1, 5, 6])
    result = call_path_length.evaluate(pool)
    assert result.outcomes() == (6,)


def test_mixed_pool():
    pool = Pool([d4, d6, d6, d8])
    result = call_path_length.evaluate(pool)
    assert result.outcomes() == (8,)


def test_simple_pool_sorted_roll_counts():
    pool = d6.pool(5)[-2:]
    result = call_path_length.evaluate(pool)
    assert result.outcomes() == (6,)


def test_simple_pool_sorted_roll_counts_low():
    pool = d6.pool(5)[:2]
    result = call_path_length.evaluate(pool)
    assert result.outcomes() == (6,)


def test_mixed_pool_sorted_roll_counts():
    pool = Pool([d4, d6, d6, d8])[-2:]
    result = call_path_length.evaluate(pool)
    assert result.outcomes() == (8,)


def test_mixed_pool_sorted_roll_counts_low():
    pool = Pool([d4, d6, d6, d8])[:2]
    result = call_path_length.evaluate(pool)
    assert result.outcomes() == (8,)


def test_range_alignment_non_int():
    pool = Pool([0.5])
    with pytest.raises(TypeError):
        result = call_path_length.evaluate(pool)
