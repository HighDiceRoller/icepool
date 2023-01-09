"""Submodule containing evaluators."""

__docformat__ = 'google'

from icepool.evaluator.basic import WrapFuncEvaluator, ExpandEvaluator, SumEvaluator, sum_evaluator, CountEvaluator, count_evaluator
from icepool.evaluator.poker import (LargestMatchingSetEvaluator,
                                     LargestMatchingSetAndOutcomeEvaluator,
                                     AllMatchingSetsEvaluator,
                                     LargestStraightEvaluator,
                                     LargestStraightAndOutcomeEvaluator)
from icepool.evaluator.comparison import (
    ComparisonEvaluator, IsSubsetEvaluator, IsProperSubsetEvaluator,
    IsSupersetEvaluator, IsProperSupersetEvaluator, IsEqualSetEvaluator,
    IsNotEqualSetEvaluator, IsDisjointSetEvaluator)
from icepool.evaluator.joint import JointEvaluator
from icepool.evaluator.adjust import FinalOutcomeMapEvaluator

__all__ = [
    'WrapFuncEvaluator', 'ExpandEvaluator', 'SumEvaluator', 'sum_evaluator',
    'CountEvaluator', 'count_evaluator', 'LargestMatchingSetEvaluator',
    'LargestMatchingSetAndOutcomeEvaluator', 'AllMatchingSetsEvaluator',
    'LargestStraightEvaluator', 'LargestStraightAndOutcomeEvaluator',
    'ComparisonEvaluator', 'IsSubsetEvaluator', 'IsProperSubsetEvaluator',
    'IsSupersetEvaluator', 'IsProperSupersetEvaluator', 'IsEqualSetEvaluator',
    'IsNotEqualSetEvaluator', 'IsDisjointSetEvaluator', 'JointEvaluator',
    'FinalOutcomeMapEvaluator'
]
