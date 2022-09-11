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

from icepool.constant import SpecialValue

Reroll = SpecialValue.Reroll
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

from icepool.die.func import (standard, d, __getattr__, bernoulli, coin,
                              one_hot, from_cumulative_quantities, from_rv,
                              min_outcome, max_outcome, align, align_range,
                              reduce, accumulate, apply, apply_sorted)

from icepool.population import Population
from icepool.die.die import implicit_convert_to_die, Die
from icepool.again import Again
from icepool.die.die_with_truth import DieWithTruth

from icepool.counts import CountsKeysView, CountsValuesView, CountsItemsView

from icepool.die.lowest_highest import lowest, highest

from icepool.pool import Pool, standard_pool, clear_pool_cache
from icepool.outcome_count_generator import OutcomeCountGenerator, NextOutcomeCountGenerator
from icepool.outcome_count_evaluator import OutcomeCountEvaluator, Order
from icepool.evaluators import (
    WrapFuncEvaluator, JointEvaluator, SumEvaluator, sum_evaluator,
    expand_evaluator, CountInEvaluator, SubsetTargetEvaluator,
    ContainsSubsetEvaluator, IntersectionSizeEvaluator,
    BestMatchingSetEvaluator, best_matching_set_evaluator,
    BestStraightEvaluator, best_straight_evaluator)

from icepool.deck import Deck
from icepool.deal import Deal

from icepool.suits import SuitGenerator

__all__ = [
    'standard', 'd', 'bernoulli', 'coin', 'one_hot', 'Die', 'Population',
    'Again', 'CountsKeysView', 'CountsValuesView', 'CountsItemsView',
    'from_cumulative_quantities', 'from_rv', 'align', 'align_range', 'lowest',
    'highest', 'min_outcome', 'max_outcome', 'reduce', 'accumulate', 'apply',
    'apply_sorted', 'Reroll', 'Unlimited', 'OutcomeCountGenerator', 'Pool',
    'standard_pool', 'OutcomeCountEvaluator', 'Order', 'JointEvaluator',
    'SumEvaluator', 'Deck', 'Deal', 'SuitGenerator', 'clear_pool_cache'
]
