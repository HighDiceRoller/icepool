""" Package for computing dice probabilities.

See [this JupyterLite distribution](https://highdiceroller.github.io/icepool/notebooks/lab/index.html)
for examples.

[Visit the project page.](https://github.com/HighDiceRoller/icepool)

General conventions:

* Unless explictly specified otherwise, all sorting is in ascending order.
* The words "min" and "max" refer to outcomes, and the words "low" and "high"
refer to dice in a pool.
"""

__docformat__ = 'google'

# Expose certain names at top-level.

from icepool.die.func import (standard, d, __getattr__, bernoulli, coin,
                              from_cweights, from_sweights, from_rv,
                              min_outcome, max_outcome, align, align_range,
                              reduce, accumulate, apply, apply_sorted)

from icepool.die.die import Die
from icepool.die.die_with_truth import DieWithTruth

from icepool.die.keep import lowest, highest

from icepool.pool.pool import Pool, standard_pool
from icepool.pool.eval import EvalPool, WrapFuncEval, JointEval, SumPool, sum_pool, enumerate_pool, FindBestSet, FindBestRun

import enum


class SpecialValue(enum.Enum):
    Reroll = 'Reroll'
    """Indicates an outcome should be rerolled (with no max depth)."""


Reroll = SpecialValue.Reroll
"""Indicates an outcome should be rerolled (with no max depth)."""

__all__ = [
    'standard', 'd', 'bernoulli', 'coin', 'Die', 'from_cweights',
    'from_sweights', 'from_rv', 'align', 'align_range', 'lowest', 'highest',
    'min_outcome', 'max_outcome', 'reduce', 'accumulate', 'apply',
    'apply_sorted', 'Reroll', 'Pool', 'standard_pool', 'EvalPool', 'JointEval',
    'SumPool'
]
