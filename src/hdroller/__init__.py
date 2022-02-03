""" Package for computing dice probabilities. """

__docformat__ = 'google'

# Expose certain names at top-level.

from hdroller.dice.func import die, standard, d, __getattr__, bernoulli, coin, from_cweights, from_sweights, from_rv, apply, mix

import hdroller.dice.base

from hdroller.dice.base import BaseDie
from hdroller.dice.zero import ZeroDie
from hdroller.dice.single import SingleDie
from hdroller.dice.multi import MultiDie

min = hdroller.dice.base.BaseDie.min
max = hdroller.dice.base.BaseDie.max
min_outcome = hdroller.dice.base.BaseDie.min_outcome
max_outcome = hdroller.dice.base.BaseDie.max_outcome

# Careful when using align, since it introduces zero-weight outcomes.
from hdroller.dice.base import align
from hdroller.dice.single import align_range

from hdroller.dice_pool import pool
from hdroller.pool_eval import PoolEval, PoolSum, pool_sum, PoolMatchingSet

__all__ = ['die', 'standard', 'd', '__getattr__', 'bernoulli', 'coin',
    'BaseDie', 'ZeroDie', 'SingleDie', 'MultiDie',
    'from_cweights', 'from_sweights', 'from_rv', 'mix',
    'min', 'max', 'min_outcome', 'max_outcome',
    'apply', 'align', 'align_range',
    'pool', 'PoolEval', 'PoolSum', 'pool_sum', 'PoolMatchingSet']
