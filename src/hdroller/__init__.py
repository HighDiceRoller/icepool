""" Package for computing dice probabilities. """

__docformat__ = 'google'

# Expose certain names at top-level.

from hdroller.die.create import Die, dice_with_common_ndim
from hdroller.die.func import standard, d, __getattr__, bernoulli, coin, from_cweights, from_sweights, from_rv, align, align_range, apply

import hdroller.die.base

from hdroller.die.base import BaseDie
from hdroller.die.empty import EmptyDie
from hdroller.die.scalar import ScalarDie
from hdroller.die.vector import VectorDie

highest = hdroller.die.base.BaseDie.highest
lowest = hdroller.die.base.BaseDie.lowest
max_outcome = hdroller.die.base.BaseDie.max_outcome
min_outcome = hdroller.die.base.BaseDie.min_outcome

from hdroller.pool import Pool, standard_pool, DicePool
from hdroller.eval_pool import EvalPool, WrapFuncEval, SumPool, sum_pool, FindBestSet, FindBestRun

import enum

class SpecialValue(enum.Enum):
    Reroll = 'Reroll'

Reroll = SpecialValue.Reroll

__all__ = ['Die', 'dice_with_common_ndim',
    'standard', 'd', '__getattr__', 'bernoulli', 'coin',
    'BaseDie', 'EmptyDie', 'ScalarDie', 'VectorDie',
    'from_cweights', 'from_sweights', 'from_rv', 'align', 'align_range',
    'lowest', 'highest', 'max_outcome', 'min_outcome',
    'apply',
    'Reroll',
    'Pool', 'standard_pool', 'DicePool',
    'EvalPool', 'WrapFuncEval', 'SumPool', 'sum_pool', 'FindBestSet', 'FindBestRun',
    'd2', 'd3', 'd4', 'd6', 'd8', 'd10', 'd12', 'd20', 'd100']
