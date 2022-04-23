""" Package for computing dice probabilities.

See [this JupyterLite distribution](https://highdiceroller.github.io/icepool/notebooks/lab/index.html) for examples.

[Visit the project page.](https://github.com/HighDiceRoller/icepool)

General conventions:

* Unless explictly specified otherwise, all sorting is in ascending order.
* The words "min" and "max" refer to outcomes, and the words "low" and "high" refer to dice in a pool.
"""

__docformat__ = 'google'

# Expose certain names at top-level.

from icepool.die.create import Die, dice_with_common_ndim
from icepool.die.func import standard, d, __getattr__, bernoulli, coin, from_cweights, from_sweights, from_rv, align, align_range, apply

import icepool.die.base

from icepool.die.base import BaseDie
from icepool.die.empty import EmptyDie
from icepool.die.scalar import ScalarDie
from icepool.die.vector import VectorDie

highest = icepool.die.base.BaseDie.highest
lowest = icepool.die.base.BaseDie.lowest
max_outcome = icepool.die.base.BaseDie.max_outcome
min_outcome = icepool.die.base.BaseDie.min_outcome

from icepool.pool.base import BasePool
from icepool.pool.pool import Pool, standard_pool, DicePool
from icepool.pool.roll import PoolRoll
from icepool.pool.eval import EvalPool, WrapFuncEval, SumPool, sum_pool, FindBestSet, FindBestRun

import enum

class SpecialValue(enum.Enum):
    Reroll = 'Reroll'

Reroll = SpecialValue.Reroll

__all__ = ['Die',
    'standard', 'd', '__getattr__', 'bernoulli', 'coin',
    'BaseDie', 'EmptyDie', 'ScalarDie', 'VectorDie',
    'from_cweights', 'from_sweights', 'from_rv', 'align', 'align_range',
    'lowest', 'highest', 'max_outcome', 'min_outcome',
    'apply', 'dice_with_common_ndim',
    'Reroll',
    'BasePool',
    'Pool', 'standard_pool', 'DicePool',
    # 'PoolRoll',  # Not needed externally due to implicit casts
    'EvalPool', 'WrapFuncEval', 'SumPool', 'sum_pool', 'FindBestSet', 'FindBestRun',
    'd2', 'd3', 'd4', 'd6', 'd8', 'd10', 'd12', 'd20', 'd100']
