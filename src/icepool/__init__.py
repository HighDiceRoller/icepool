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
"""

__docformat__ = 'google'

from typing import Final

from icepool.typing import Outcome, Order, RerollType

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

from icepool.population.func import (d, __getattr__, coin, one_hot,
                                     cartesian_product,
                                     from_cumulative_quantities, from_rv,
                                     min_outcome, max_outcome, align,
                                     align_range, reduce, accumulate, apply,
                                     apply_sorted)

from icepool.population.base import Population
from icepool.population.die import implicit_convert_to_die, Die
from icepool.population.again import Again
from icepool.population.die_with_truth import DieWithTruth

from icepool.counts import CountsKeysView, CountsValuesView, CountsItemsView

from icepool.population.lowest_highest import lowest, highest, sum_lowest, sum_highest

from icepool.generator.pool import Pool, standard_pool
from icepool.generator.outcome_count_generator import OutcomeCountGenerator, NextOutcomeCountGenerator, implicit_convert_to_generator
from icepool.evaluator.outcome_count_evaluator import OutcomeCountEvaluator

from icepool.population.deck import Deck
from icepool.generator.deal import Deal

from icepool.generator.suit import SuitGenerator

import icepool.evaluator as evaluator

__all__ = [
    'd', 'coin', 'one_hot', 'cartesian_product', 'Outcome', 'Die', 'Population',
    'Again', 'CountsKeysView', 'CountsValuesView', 'CountsItemsView',
    'from_cumulative_quantities', 'from_rv', 'align', 'align_range', 'lowest',
    'highest', 'sum_lowest', 'sum_highest', 'min_outcome', 'max_outcome',
    'reduce', 'accumulate', 'apply', 'apply_sorted', 'Reroll', 'RerollType',
    'OutcomeCountGenerator', 'Pool', 'standard_pool', 'OutcomeCountEvaluator',
    'Order', 'evaluator', 'Deck', 'Deal', 'SuitGenerator'
]
