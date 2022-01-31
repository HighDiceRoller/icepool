# Expose certain names at top-level.

from hdroller.dice.func import die, standard, __getattr__, bernoulli, coin, from_cweights, from_sweights, from_rv, apply, mix

# Careful when using this one, since it introduces zero-weight outcomes.
from hdroller.dice.base import _align

import hdroller.dice.base
min = hdroller.dice.base.BaseDie.min
max = hdroller.dice.base.BaseDie.max

from hdroller.dice_pool import pool
from hdroller.pool_eval import PoolEval, pool_sum
