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
* When used with `MultisetEvaluator`, the entire evaluation is rerolled.
"""

# Expose certain names at top-level.

import icepool.population.func
from icepool.population.func import (d, __getattr__, coin, one_hot,
                                     cartesian_product,
                                     from_cumulative_quantities, from_rv,
                                     min_outcome, max_outcome, align,
                                     align_range, reduce, accumulate, apply,
                                     outcome_function)

from icepool.population.base import Population
from icepool.population.die import implicit_convert_to_die, Die
from icepool.population.again import Again
from icepool.population.die_with_truth import DieWithTruth

from icepool.collections import CountsKeysView, CountsValuesView, CountsItemsView

from icepool.population.keep import lowest, highest, middle

from icepool.generator.pool import Pool, standard_pool

from icepool.generator.multiset_generator import MultisetGenerator, NextMultisetGenerator
from icepool.generator.alignment import Alignment
from icepool.evaluator.multiset_evaluator import MultisetEvaluator

from icepool.population.deck import Deck
from icepool.generator.deal import Deal

from icepool.expression.multiset_expression import MultisetExpression, implicit_convert_to_expression
from icepool.expression.multiset_function import multiset_function

import icepool.expression as expression
import icepool.generator as generator
import icepool.evaluator as evaluator

import icepool.typing as typing

__all__ = [
    'd', 'coin', 'one_hot', 'cartesian_product', 'Outcome', 'Die', 'Population',
    'Again', 'CountsKeysView', 'CountsValuesView', 'CountsItemsView',
    'from_cumulative_quantities', 'from_rv', 'align', 'align_range', 'lowest',
    'highest', 'middle', 'min_outcome', 'max_outcome', 'reduce', 'accumulate',
    'apply', 'outcome_function', 'Reroll', 'RerollType', 'Pool',
    'standard_pool', 'MultisetGenerator', 'Alignment', 'MultisetExpression',
    'MultisetEvaluator', 'Order', 'Deck', 'Deal', 'multiset_function', 'typing',
    'evaluator'
]
