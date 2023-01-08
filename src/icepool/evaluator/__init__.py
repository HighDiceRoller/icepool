"""Submodule containing evaluators."""

__docformat__ = 'google'

from icepool.evaluator.basic import WrapFuncEvaluator, ExpandEvaluator, SumEvaluator, sum_evaluator, CountEvaluator, count_evaluator
from icepool.evaluator.poker import (LargestMatchingSetEvaluator,
                                     LargestMatchingSetAndOutcomeEvaluator,
                                     AllMatchingSetsEvaluator,
                                     LargestStraightEvaluator,
                                     LargestStraightAndOutcomeEvaluator)
from icepool.evaluator.comparison import (
    IsSubsetEvaluator, IsProperSubsetEvaluator, IsSupersetEvaluator,
    IsProperSupersetEvaluator, IsEqualSetEvaluator, IsNotEqualSetEvaluator,
    IsDisjointSetEvaluator)
from icepool.evaluator.joint import JointEvaluator
from icepool.evaluator.adjust import AdjustIntCountEvaluator, FinalOutcomeMapEvaluator

__all__ = [
    'WrapFuncEvaluator', 'ExpandEvaluator', 'SumEvaluator', 'sum_evaluator',
    'CountEvaluator', 'count_evaluator', 'LargestMatchingSetEvaluator',
    'LargestMatchingSetAndOutcomeEvaluator', 'AllMatchingSetsEvaluator',
    'LargestStraightEvaluator', 'LargestStraightAndOutcomeEvaluator',
    'IsSubsetEvaluator', 'IsProperSubsetEvaluator', 'IsSupersetEvaluator',
    'IsProperSupersetEvaluator', 'IsEqualSetEvaluator',
    'IsNotEqualSetEvaluator', 'IsDisjointSetEvaluator', 'JointEvaluator',
    'AdjustIntCountEvaluator', 'FinalOutcomeMapEvaluator'
]
