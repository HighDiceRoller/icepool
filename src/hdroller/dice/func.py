import hdroller
import hdroller.collections
import hdroller.dice.base
import hdroller.dice.single
import hdroller.dice.multi

from collections import defaultdict
import itertools
import math

def _die_from_checked_dict(d, ndim=None):
    data = hdroller.collections.FrozenSortedDict(d)
    
    if ndim is not None:
        if not isinstance(ndim, int):
            raise TypeError('ndim must be an integer.')
        if ndim == 1:
            return hdroller.dice.single.SingleDie(data, 1)
        else:
            return hdroller.dice.multi.MultiDie(data, ndim)
    
    ndim = None
    for outcome in data.keys():
        try:
            if ndim is None:
                ndim = len(outcome)
            elif ndim != len(outcome):
                return hdroller.dice.single.SingleDie(data, 1)
        except TypeError:
            return hdroller.dice.single.SingleDie(data, 1)

    if ndim == 1:
        d = { k[0] : v for k, v in data.items() }
        return _die_from_checked_dict(d, ndim=ndim)
    
    return hdroller.dice.multi.MultiDie(data, ndim)

def die(arg, min_outcome=None, ndim=None, remove_zero_weights=True):
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
        ndim: If provided, the die will have the given number of dimensions.
    """
    if isinstance(arg, hdroller.dice.base.BaseDie):
        return arg
    
    if min_outcome is not None:
        data = {min_outcome + i : weight for i, weight in enumerate(arg) if not remove_zero_weights or weight > 0}
    elif hasattr(arg, 'keys'):
        data = { k : arg[k] for k in sorted(arg.keys()) if not remove_zero_weights or arg[k] > 0 }
    elif hasattr(arg, '__iter__'):
        data = { k : v for k, v in sorted(arg) if not remove_zero_weights or v > 0 }
    else:
        # Treat arg as the only possible value.
        data = {arg : 1}
    
    if len(data) == 0:
        return None
    
    for value in data.values():
        if not isinstance(value, int):
            raise TypeError('Values must be ints.')
    
    return _die_from_checked_dict(data, ndim=ndim)

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

def from_cweights(outcomes, cweights, ndim=None):
    prev = 0
    d = {}
    for outcome, weight in zip(outcomes, cweights):
        if weight - prev > 0:
            d[outcome] = weight - prev
            prev = weight
    return _die_from_checked_dict(d, ndim=ndim)
    
def from_sweights(outcomes, sweights, ndim=None):
    d = {}
    for i, outcome in enumerate(outcomes):
        if i < len(outcomes) - 1:
            weight = sweights[i] - sweights[i+1]
        else:
            weight = sweights[i]
        if weight > 0:
            d[outcome] = weight
    return _die_from_checked_dict(d, ndim=ndim)

def from_rv(rv, outcomes, denominator, **kwargs):
    """
    Args:
        rv: A rv object (as scipy.stats).
        outcomes: An iterable of ints or floats that will be the outcomes of the resulting die.
            If the distribution is discrete, outcomes must be ints.
        denominator: The total weight of the resulting die will be set to this.
        **kwargs: These will be provided to rv.cdf().
    """
    if hasattr(rv, 'pdf'):
        # Continuous distributions use midpoints.
        midpoints = [(a + b) / 2 for a, b in zip(outcomes[:-1], outcomes[1:])]
        cdf = rv.cdf(midpoints, **kwargs)
        cweights = tuple(int(round(x * denominator)) for x in cdf) + (denominator,)
    else:
        cdf = rv.cdf(outcomes, **kwargs)
        cweights = tuple(int(round(x * denominator)) for x in cdf)
    return from_cweights(outcomes, cweights)
    
def apply(func, *dice, ndim=None):
    dice = [die(d) for d in dice]
    data = defaultdict(int)
    for t in itertools.product(*(d.items() for d in dice)):
        outcomes, weights = zip(*t)
        data[func(*outcomes)] += math.prod(weights)
    
    return die(data, ndim=ndim)

def mix(*dice, mix_weights=None):
    """
    Constructs a die from a mixture of the arguments,
    equivalent to rolling a die and then choosing one of the arguments
    based on the resulting face rolled.
    Dice (or anything castable to a die) may be provided as a list or as a variable number of arguments.
    mix_weights: An iterable of one int per argument.
        If not provided, all dice are mixed uniformly.
    """
    dice = hdroller.dice.base._align(*dice)
    ndim = None
    for d in dice:
        if ndim is None:
            ndim = d.ndim()
        elif d.ndim() != ndim:
            ndim = 1
    
    weight_product = math.prod(d.total_weight() for d in dice)
    
    if mix_weights is None:
        mix_weights = (1,) * len(dice)
    
    data = defaultdict(int)
    for d, mix_weight in zip(dice, mix_weights):
        factor = mix_weight * weight_product // d.total_weight()
        for outcome, weight in zip(d.outcomes(), d.weights()):
            data[outcome] += weight * factor
    return die(data, ndim=ndim)
