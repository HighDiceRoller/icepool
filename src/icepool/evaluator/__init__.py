"""Submodule containing evaluators."""

__docformat__ = 'google'

from icepool.evaluator.basic import (ExpandEvaluator, SumEvaluator,
                                     sum_evaluator, SizeEvaluator,
                                     size_evaluator, AnyEvaluator,
                                     any_evaluator)
from icepool.evaluator.poker import (
    HighestOutcomeAndCountEvaluator, highest_outcome_and_count_evaluator,
    LargestCountEvaluator, largest_count_evaluator,
    LargestCountAndOutcomeEvaluator, largest_count_and_outcome_evaluator,
    CountSubsetEvaluator, AllCountsEvaluator, LargestStraightEvaluator,
    largest_straight_evaluator, LargestStraightAndOutcomeEvaluator,
    largest_straight_and_outcome_evaluator_low,
    largest_straight_and_outcome_evaluator_high, AllStraightsEvaluator,
    all_straights_evaluator, AllStraightsReduceCountsEvaluator)
from icepool.evaluator.comparison import (
    ComparisonEvaluator, IsSubsetEvaluator, IsProperSubsetEvaluator,
    IsSupersetEvaluator, IsProperSupersetEvaluator, IsEqualSetEvaluator,
    IsNotEqualSetEvaluator, IsDisjointSetEvaluator)
from icepool.evaluator.keep import KeepEvaluator, keep_evaluator
from icepool.evaluator.argsort import ArgsortEvaluator
from icepool.evaluator.multiset_function import MultisetFunctionEvaluator

__all__ = [
    'ExpandEvaluator', 'SumEvaluator', 'sum_evaluator', 'SizeEvaluator',
    'size_evaluator', 'AnyEvaluator', 'any_evaluator',
    'HighestOutcomeAndCountEvaluator', 'highest_outcome_and_count_evaluator',
    'LargestCountEvaluator', 'largest_count_evaluator',
    'LargestCountAndOutcomeEvaluator', 'largest_count_and_outcome_evaluator',
    'CountSubsetEvaluator', 'AllCountsEvaluator', 'LargestStraightEvaluator',
    'largest_straight_evaluator', 'LargestStraightAndOutcomeEvaluator',
    'largest_straight_and_outcome_evaluator_low',
    'largest_straight_and_outcome_evaluator_high', 'AllStraightsEvaluator',
    'all_straights_evaluator', 'AllStraightsReduceCountsEvaluator',
    'ComparisonEvaluator', 'IsSubsetEvaluator', 'IsProperSubsetEvaluator',
    'IsSupersetEvaluator', 'IsProperSupersetEvaluator', 'IsEqualSetEvaluator',
    'IsNotEqualSetEvaluator', 'IsDisjointSetEvaluator', 'KeepEvaluator',
    'keep_evaluator', 'ArgsortEvaluator', 'MultisetFunctionEvaluator'
]
