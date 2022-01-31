__docformat__ = 'google'

# Expose certain names at top-level.

from hdroller.dice.func import die, standard, __getattr__, bernoulli, coin, from_cweights, from_sweights, from_rv, apply, mix

import hdroller.dice.base
# Careful when using _align, since it introduces zero-weight outcomes.
from hdroller.dice.base import _align

min = hdroller.dice.base.BaseDie.min
max = hdroller.dice.base.BaseDie.max

from hdroller.dice_pool import pool
from hdroller.pool_eval import PoolEval, pool_sum

"""
__all__ = ['die', 'standard', '__getattr__', 'bernoulli', 'coin', 'from_cweights', 'from_sweights', 'from_rv', 'apply', 'mix',
    '_align', 'min', 'max', 'pool', 'PoolEval', 'pool_sum',
    'hdroller.dice.base']
"""