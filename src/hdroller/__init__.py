""" Package for computing dice probabilities. """

__docformat__ = 'google'

# Expose certain names at top-level.

from hdroller.die.func import Die, standard, d, __getattr__, bernoulli, coin, from_cweights, from_sweights, from_rv, mix, if_else, align, align_range, check_ndim, apply

import hdroller.die.base

from hdroller.die.base import BaseDie
from hdroller.die.scalar import ScalarDie
from hdroller.die.vector import VectorDie

min = hdroller.die.base.BaseDie.min
max = hdroller.die.base.BaseDie.max
min_outcome = hdroller.die.base.BaseDie.min_outcome
max_outcome = hdroller.die.base.BaseDie.max_outcome

from hdroller.pool import Pool, DicePool
from hdroller.eval_pool import EvalPool, SumPool, sum_pool, FindMatchingSets

__all__ = ['Die', 'standard', 'd', '__getattr__', 'bernoulli', 'coin',
    'BaseDie', 'ScalarDie', 'VectorDie',
    'from_cweights', 'from_sweights', 'from_rv', 'mix', 'if_else', 'align', 'align_range', 'check_ndim',
    'min', 'max', 'min_outcome', 'max_outcome',
    'apply',
    'Pool', 'DicePool', 'EvalPool', 'SumPool', 'sum_pool', 'FindMatchingSets',
    'd2', 'd3', 'd4', 'd6', 'd8', 'd10', 'd12', 'd20', 'd100']
