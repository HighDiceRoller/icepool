__docformat__ = 'google'

# Expose certain names at top-level.

from hdroller.dice.func import die, standard, __getattr__, bernoulli, coin, from_cweights, from_sweights, from_rv, apply, mix

import hdroller.dice.base

from hdroller.dice.base import BaseDie
from hdroller.dice.zero import ZeroDie
from hdroller.dice.single import SingleDie
from hdroller.dice.multi import MultiDie

min = hdroller.dice.base.BaseDie.min
max = hdroller.dice.base.BaseDie.max

# Careful when using _align, since it introduces zero-weight outcomes.
from hdroller.dice.base import _align

from hdroller.dice_pool import pool
from hdroller.pool_eval import PoolEval, pool_sum

__all__ = ['die', 'standard', '__getattr__', 'bernoulli', 'coin', 'BaseDie', 'ZeroDie', 'SingleDie', 'MultiDie', 'from_cweights', 'from_sweights', 'from_rv', 'apply', 'mix', 'min', 'max', '_align',
    'pool', 'PoolEval', 'pool_sum']