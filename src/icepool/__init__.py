"""Package for computing dice and card probabilities.

Starting with `v0.25.1`, you can replace `latest` in the URL with an old version
number to get the documentation for that version.

See [this JupyterLite distribution](https://highdiceroller.github.io/icepool/notebooks/lab/index.html)
for examples.

[Visit the project page.](https://github.com/HighDiceRoller/icepool)

General conventions:

* Instances are immutable (apart from internal caching). Anything that looks
    like it mutates an instance actually returns a separate instance with the
    change.
"""

__docformat__ = 'google'

__version__ = '1.6.1'

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
* To reroll with limited depth, use `Die.reroll()`, or `Again` with no
    modification.
* When used with `MultisetEvaluator`, the entire evaluation is rerolled.
"""

# Expose certain names at top-level.

from icepool.function import (
    d, z, __getattr__, coin, stochastic_round, one_hot, iter_cartesian_product,
    from_cumulative, from_rv, pointwise_max, pointwise_min, min_outcome,
    max_outcome, consecutive, sorted_union, commonize_denominator, reduce,
    accumulate, map, map_function, map_and_time, map_to_pool)

from icepool.population.base import Population
from icepool.population.die import implicit_convert_to_die, Die
from icepool.collection.vector import cartesian_product, tupleize, vectorize, Vector
from icepool.collection.symbols import Symbols
from icepool.population.again import AgainExpression

Again: Final = AgainExpression(is_additive=True)
"""A symbol indicating that the die should be rolled again, usually with some operation applied.

This is designed to be used with the `Die()` constructor.
`AgainExpression`s should not be fed to functions or methods other than
`Die()`, but it can be used with operators. Examples:

* `Again + 6`: Roll again and add 6.
* `Again + Again`: Roll again twice and sum.

The `again_count`, `again_depth`, and `again_end` arguments to `Die()`
affect how these arguments are processed. At most one of `again_count` or
`again_depth` may be provided; if neither are provided, the behavior is as
`again_depth=1.

For finer control over rolling processes, use e.g. `Die.map()` instead.

#### Count mode

When `again_count` is provided, we start with one roll queued and execute one 
roll at a time. For every `Again` we roll, we queue another roll.
If we run out of rolls, we sum the rolls to find the result. If the total number
of rolls (not including the initial roll) would exceed `again_count`, we reroll
the entire process, effectively conditioning the process on not rolling more
than `again_count` extra dice.

This mode only allows "additive" expressions to be used with `Again`, which
means that only the following operators are allowed:

* Binary `+`
* `n @ AgainExpression`, where `n` is a non-negative `int` or `Population`.

Furthermore, the `+` operator is assumed to be associative and commutative.
For example, `str` or `tuple` outcomes will not produce elements with a definite
order.

#### Depth mode

When `again_depth=0`, `again_end` is directly substituted
for each occurence of `Again`. For other values of `again_depth`, the result for
`again_depth-1` is substituted for each occurence of `Again`.

If `again_end=icepool.Reroll`, then any `AgainExpression`s in the final depth
are rerolled.

#### Rerolls

`Reroll` only rerolls that particular die, not the entire process. Any such
rerolls do not count against the `again_count` or `again_depth` limit.

If `again_end=icepool.Reroll`:
* Count mode: Any result that would cause the number of rolls to exceed
    `again_count` is rerolled.
* Depth mode: Any `AgainExpression`s in the final depth level are rerolled.
"""

from icepool.population.die_with_truth import DieWithTruth

from icepool.collection.counts import CountsKeysView, CountsValuesView, CountsItemsView

from icepool.population.keep import lowest, highest, middle

from icepool.generator.pool import Pool, standard_pool
from icepool.generator.keep import KeepGenerator
from icepool.generator.compound_keep import CompoundKeepGenerator
from icepool.generator.mixture import MixtureGenerator

from icepool.generator.multiset_generator import MultisetGenerator, InitialMultisetGenerator, NextMultisetGenerator
from icepool.generator.alignment import Alignment
from icepool.evaluator.multiset_evaluator import MultisetEvaluator

from icepool.population.deck import Deck
from icepool.generator.deal import Deal
from icepool.generator.multi_deal import MultiDeal

from icepool.expression.multiset_expression import MultisetExpression, implicit_convert_to_expression
from icepool.expression.multiset_function import multiset_function

import icepool.expression as expression
import icepool.generator as generator
import icepool.evaluator as evaluator

import icepool.typing as typing

__all__ = [
    'd', 'z', 'coin', 'stochastic_round', 'one_hot', 'Outcome', 'Die',
    'Population', 'tupleize', 'vectorize', 'Vector', 'Symbols', 'Again',
    'CountsKeysView', 'CountsValuesView', 'CountsItemsView', 'from_cumulative',
    'from_rv', 'pointwise_max', 'pointwise_min', 'lowest', 'highest', 'middle',
    'min_outcome', 'max_outcome', 'consecutive', 'sorted_union',
    'commonize_denominator', 'reduce', 'accumulate', 'map', 'map_function',
    'map_and_time', 'map_to_pool', 'Reroll', 'RerollType', 'Pool',
    'standard_pool', 'MultisetGenerator', 'MultisetExpression',
    'MultisetEvaluator', 'Order', 'Deck', 'Deal', 'MultiDeal',
    'multiset_function', 'function', 'typing', 'evaluator'
]
