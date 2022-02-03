""" Package for computing dice probabilities. """

__docformat__ = 'google'

# Expose certain names at top-level.

from hdroller.dice.func import Die, standard, d, __getattr__, bernoulli, coin, from_cweights, from_sweights, from_rv, mix, align, align_range, apply

import hdroller.dice.base

from hdroller.dice.base import BaseDie
from hdroller.dice.zero import ZeroDie
from hdroller.dice.single import SingleDie
from hdroller.dice.multi import MultiDie

min = hdroller.dice.base.BaseDie.min
max = hdroller.dice.base.BaseDie.max
min_outcome = hdroller.dice.base.BaseDie.min_outcome
max_outcome = hdroller.dice.base.BaseDie.max_outcome

from hdroller.dice_pool import Pool
from hdroller.pool_eval import PoolEval, PoolSum, pool_sum, PoolMatchingSet

__all__ = ['Die', 'standard', 'd', '__getattr__', 'bernoulli', 'coin',
    'BaseDie', 'ZeroDie', 'SingleDie', 'MultiDie',
    'from_cweights', 'from_sweights', 'from_rv', 'mix', 'align', 'align_range',
    'min', 'max', 'min_outcome', 'max_outcome',
    'apply',
    'Pool', 'PoolEval', 'PoolSum', 'pool_sum', 'PoolMatchingSet']
