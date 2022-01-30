import hdroller
import hdroller._die.data
import hdroller._die.base
import hdroller._die.single
import hdroller._die.multi

from collections import defaultdict
import itertools
import math

def _die_from_checked_dict(d, *, force_single=False):
    data = hdroller._die.data.DieData(d)
    
    if force_single:
        return hdroller._die.single.SingleDie(data)
    
    ndim = None
    for outcome in data.keys():
        try:
            if ndim is None:
                ndim = len(outcome)
            elif ndim != len(outcome):
                return hdroller._die.single.SingleDie(data)
        except TypeError:
            return hdroller._die.single.SingleDie(data)
    
    return hdroller._die.multi.MultiDie(data)

def die(arg, min_outcome=None, *, force_single=False, remove_zero_weights=True):
    """
    Args:
        arg: This can be one of the following:
            A die, which will be returned itself.
            An iterable of weights, with min_outcome set to an integer.
                The outcomes will be integers starting at min_outcome.
            A mapping from outcomes to weights.
            An iterable of pairs of outcomes and weights.
            A single hashable and comparable value.
                There will be a single outcome equal to the argument, with weight 1.
        force_single: If True, the die is treated as univariate even if its outcomes are iterable.
    """
    if isinstance(arg, hdroller._die.base.BaseDie):
        return arg
    
    # TODO: check weights are int, return None if no elements
    
    if min_outcome is not None:
        data = {min_outcome + i : weight for i, weight in enumerate(arg) if not remove_zero_weights or weight > 0}
    elif hasattr(arg, 'keys'):
        data = { k : arg[k] for k in sorted(arg.keys()) if not remove_zero_weights or arg[k] > 0 }
    elif hasattr(arg, '__iter__'):
        data = { k : v for k, v in sorted(arg) if not remove_zero_weights or v > 0 }
    else:
        # Treat arg as the only possible value.
        data = {arg : 1}
    
    return _die_from_checked_dict(data, force_single=force_single)

def standard(num_sides):
    return die([1] * num_sides, min_outcome=1)

def __getattr__(key):
    if key[0] == 'd':
        try:
            return standard(int(key[1:]))
        except ValueError:
            pass
    raise AttributeError(key)

def bernoulli(n, d):
    return die({False : d - n, True : n})

coin = bernoulli

def from_cweights(outcomes, cweights, *, force_single=False):
    prev = 0
    d = {}
    for outcome, weight in zip(outcomes, cweights):
        if weight - prev > 0:
            d[outcome] = weight - prev
            prev = weight
    return _die_from_checked_dict(d, force_single=force_single)
    
def from_sweights(outcomes, sweights, *, force_single=False):
    d = {}
    for i, outcome in enumerate(outcomes):
        if i < len(outcomes) - 1:
            weight = sweights[i] - sweights[i+1]
        else:
            weight = sweights[i]
        if weight > 0:
            d[outcome] = weight
    return _die_from_checked_dict(d, force_single=force_single)

def from_rv(rv, outcomes, d):
    raise NotImplementedError("TODO")
    
def apply(func, *dice, force_single=False):
    dice = [die(d) for d in dice]
    data = defaultdict(int)
    for t in itertools.product(*(d.items() for d in dice)):
        outcomes, weights = zip(*t)
        data[func(*outcomes)] += math.prod(weights)
    
    return die(data, force_single=force_single)

def mix(*dice, mix_weights=None):
    """
    Constructs a die from a mixture of the arguments,
    equivalent to rolling a die and then choosing one of the arguments
    based on the resulting face rolled.
    Dice (or anything castable to a die) may be provided as a list or as a variable number of arguments.
    mix_weights: An iterable of one int per argument.
        If not provided, all dice are mixed uniformly.
    """
    dice = hdroller._die.base._align(*dice)
    force_single = any(die.is_single for die in dice)
    
    weight_product = math.prod(die.total_weight() for die in dice)
    
    if mix_weights is None:
        mix_weights = (1,) * len(dice)
    
    data = defaultdict(int)
    for die, mix_weight in zip(dice, mix_weights):
        factor = mix_weight * weight_product // die.total_weight()
        for outcome, weight in zip(die.outcomes(), die.weights()):
            data[outcome] += weight * factor
    return hdroller.die(data, force_single=force_single)