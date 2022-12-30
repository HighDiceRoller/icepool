"""Package for computing dice and card probabilities.

See [this JupyterLite distribution](https://highdiceroller.github.io/icepool/notebooks/lab/index.html)
for examples.

[Visit the project page.](https://github.com/HighDiceRoller/icepool)

General conventions:

* Instances are immutable (apart from internal caching). Anything that looks
    like it mutates an instance actually returns a separate instance with the
    change.
* Unless explictly specified otherwise, all sorting is in ascending order.
* Unless explictly specified otherwise, elements with zero quantity, rolls, etc.
    are considered.
* The words "min" and "max" refer to outcomes, and the words "low" and "high"
refer to dice in a pool.
"""

__docformat__ = 'google'

from typing import Final

from icepool.constant import Order, RerollType
from icepool.typing import Outcome

Reroll: Final = RerollType.Reroll
"""Indicates that an outcome should be rerolled (with unlimited depth).

This can be used in place of outcomes in many places. See individual function
and method descriptions for details.

This effectively removes the outcome from the probability space, along with its
contribution to the denominator.

This can be used for conditional probability by removing all outcomes not
consistent with the given observations.

Operation in specific cases:

* When used with `Again`, only that stage is rerolled, not the entire `Again`
    tree.
* To reroll with limited depth, use `Die.reroll()`, or `Again()` with no
    modification.
* When used with `OutcomeCountEvaluator`, the entire evaluation is rerolled.
"""

# Expose certain names at top-level.

from icepool.population.func import (standard, d, __getattr__, bernoulli, coin,
                                     one_hot, cartesian_product,
                                     from_cumulative_quantities, from_rv,
                                     min_outcome, max_outcome, align,
                                     align_range, reduce, accumulate, apply,
                                     apply_sorted)

from icepool.population.base import Population
from icepool.population.die import implicit_convert_to_die, Die
from icepool.population.again import Again
from icepool.population.die_with_truth import DieWithTruth

from icepool.counts import CountsKeysView, CountsValuesView, CountsItemsView

from icepool.population.lowest_highest import sum_lowest, sum_highest

from icepool.generator.pool import Pool, standard_pool, clear_pool_cache
from icepool.generator.outcome_count_generator import OutcomeCountGenerator, NextOutcomeCountGenerator
from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator
from icepool.evaluator.evaluators import (
    WrapFuncEvaluator, JointEvaluator, SumEvaluator, sum_evaluator,
    ExpandEvaluator, expand_evaluator, CountInEvaluator, count_unique_evaluator,
    SubsetTargetEvaluator, ContainsSubsetEvaluator, IntersectionSizeEvaluator,
    LargestMatchingSetEvaluator, LargestMatchingSetAndOutcomeEvaluator,
    AllMatchingSetsEvaluator, LargestStraightEvaluator,
    LargestStraightAndOutcomeEvaluator)

from icepool.population.deck import Deck
from icepool.generator.deal import Deal

from icepool.generator.generators import SuitGenerator

__all__ = [
    'standard', 'd', 'bernoulli', 'coin', 'one_hot', 'cartesian_product',
    'Outcome', 'Die', 'Population', 'Again', 'CountsKeysView',
    'CountsValuesView', 'CountsItemsView', 'from_cumulative_quantities',
    'from_rv', 'align', 'align_range', 'sum_lowest', 'sum_highest',
    'min_outcome', 'max_outcome', 'reduce', 'accumulate', 'apply',
    'apply_sorted', 'Reroll', 'RerollType', 'OutcomeCountGenerator', 'Pool',
    'standard_pool', 'OutcomeCountEvaluator', 'Order', 'JointEvaluator',
    'SumEvaluator', 'ExpandEvaluator', 'Deck', 'Deal', 'SuitGenerator',
    'clear_pool_cache'
]
