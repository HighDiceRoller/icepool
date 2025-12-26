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

__version__ = '2.2.1'

from typing import Final

from icepool.typing import Outcome, RerollType, NoCacheType
from icepool.order import Order, ConflictingOrderError, UnsupportedOrder
from icepool.map_tools.common import Break

Reroll: Final = RerollType.Reroll
"""Indicates that an outcome should be rerolled (with unlimited depth).

This effectively removes the outcome from the probability space, along with its
contribution to the denominator.

This can be used for conditional probability by removing all outcomes not
consistent with the given observations.

Operation in specific cases:

* If sent to the constructor of `Die`, it and the corresponding quantity is
    dropped.
* When used with `Again` or `map(repeat)`, only that stage is rerolled, not the 
    entire rolling process.
* To reroll with limited depth, use `Die.reroll()`, or `Again` with no
    modification.
* When used with `MultisetEvaluator`, this currently has the same meaning as
    `Restart`. Prefer using `Restart` in this case.
"""
Restart: Final = RerollType.Restart
"""Indicates that a rolling process should be restarted (with unlimited depth).

`Restart` effectively removes the sequence of events from the probability space,
along with its contribution to the denominator.

`Restart` can be used for conditional probability by removing all sequences of 
events not consistent with the given observations.

`Restart` can be used with `again_count`, `map(repeat)`, or `MultisetEvaluator`. 
When sent to the constructor of `Die`, it has the same effect as `Reroll`; 
prefer using `Reroll` in this case.

`Restart` can NOT be used with `again_depth`, but `Reroll` can.
"""

REROLL_TYPES: Final = (Reroll, Restart)
"""Explicitly defined since Enum.__contains__ requires that the queried value be hashable."""

NoCache: Final = NoCacheType.NoCache
"""Indicates that caching should not be performed. Exact meaning depends on context."""

# Expose certain names at top-level.

from icepool.function import (d, z, __getattr__, coin, stochastic_round,
                              one_hot, from_cumulative, from_rv, pointwise_max,
                              pointwise_min, min_outcome, max_outcome,
                              consecutive, sorted_union,
                              harmonize_denominators)
from icepool.map_tools.function import (reduce, accumulate, map, map_function,
                                        map_and_time, mean_time_to_absorb,
                                        map_to_pool)

from icepool.population.base import Population
from icepool.population.die import implicit_convert_to_die, Die
from icepool.expand import iter_cartesian_product, cartesian_product, tupleize, vectorize
from icepool.collection.vector import Vector
from icepool.collection.vector_with_truth_only import VectorWithTruthOnly
from icepool.collection.symbols import Symbols
from icepool.population.again import AgainExpression

Again: Final = AgainExpression(is_additive=True)
"""A symbol indicating that the die should be rolled again, usually with some operation applied.

This is designed to be used with the `Die()` constructor.
`AgainExpression`s should not be fed to functions or methods other than
`Die()` (or indirectly via `map()`), but they can be used with operators.
Examples:

* `Again + 6`: Roll again and add 6.
* `Again + Again`: Roll again twice and sum.

The `again_count`, `again_depth`, and `again_end` arguments to `Die()`
affect how these arguments are processed. At most one of `again_count` or
`again_depth` may be provided; if neither are provided, the behavior is as
`again_depth=1`.

For finer control over rolling processes, use e.g. `Die.map()` instead.

#### Count mode

When `again_count` is provided, we start with one roll queued and execute one 
roll at a time. For every `Again` we roll, we queue another roll.
If we run out of rolls, we sum the rolls to find the result. We evaluate up to
`again_count` extra rolls. If, at this point, there are still dice remaining:

* `Restart`: If there would be dice over the limit, we restart the entire 
    process from the beginning, effectively conditioning the process against
    this sequence of events.
* `Reroll`: Any remaining dice can't produce more `Again`s.
* `outcome`: Any remaining dice are each treated as the given outcome.
* `None`: Any remaining dice are treated as zero.

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

If `again_end=Reroll`, then any `AgainExpression`s in the final depth
are rerolled. `Restart` cannot be used with `again_depth`.
"""

from icepool.population.die_with_truth import DieWithTruth

from icepool.collection.counts import CountsKeysView, CountsValuesView, CountsItemsView

from icepool.population.keep import lowest, highest, middle

from icepool.generator.pool import Pool, standard_pool, d_pool, z_pool
from icepool.generator.keep import KeepGenerator
from icepool.generator.compound_keep import CompoundKeepGenerator

from icepool.generator.multiset_generator import MultisetGenerator
from icepool.generator.multiset_tuple_generator import MultisetTupleGenerator
from icepool.generator.weightless import WeightlessGenerator
from icepool.evaluator.multiset_evaluator import MultisetEvaluator

from icepool.population.deck import Deck
from icepool.generator.deal import Deal
from icepool.generator.multi_deal import MultiDeal

from icepool.expression.multiset_expression import MultisetExpression, implicit_convert_to_expression
from icepool.evaluator.multiset_function import multiset_function
from icepool.expression.multiset_parameter import MultisetParameter, MultisetTupleParameter
from icepool.expression.multiset_mixture import MultisetMixture

from icepool.population.format import format_probability_inverse

from icepool.wallenius import Wallenius

import icepool.generator as generator
import icepool.evaluator as evaluator
import icepool.operator as operator

import icepool.typing as typing
from icepool.expand import Expandable

__all__ = [
    'd', 'z', 'coin', 'stochastic_round', 'one_hot', 'Outcome', 'Die',
    'Population', 'tupleize', 'vectorize', 'Vector', 'Symbols', 'Again',
    'CountsKeysView', 'CountsValuesView', 'CountsItemsView', 'from_cumulative',
    'from_rv', 'pointwise_max', 'pointwise_min', 'lowest', 'highest', 'middle',
    'min_outcome', 'max_outcome', 'consecutive', 'sorted_union',
    'harmonize_denominators', 'reduce', 'accumulate', 'map', 'map_function',
    'map_and_time', 'mean_time_to_absorb', 'map_to_pool', 'Reroll', 'Restart',
    'Break', 'RerollType', 'Pool', 'd_pool', 'z_pool', 'MultisetGenerator',
    'MultisetExpression', 'MultisetEvaluator', 'Order',
    'ConflictingOrderError', 'UnsupportedOrder', 'Deck', 'Deal', 'MultiDeal',
    'multiset_function', 'MultisetParameter', 'MultisetTupleParameter',
    'NoCache', 'function', 'typing', 'evaluator', 'format_probability_inverse',
    'Wallenius'
]
