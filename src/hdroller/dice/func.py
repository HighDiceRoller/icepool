import hdroller
from hdroller.collections import FrozenSortedWeights
import hdroller.dice.base
import hdroller.dice.multi
import hdroller.dice.single
import hdroller.dice.zero

from collections import defaultdict
import itertools
import math

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
        
    data = _make_data(arg, min_outcome, remove_zero_weights)
    
    if len(data) == 0:
        return None
        
    ndim = _calc_ndim(data, ndim)
    
    if ndim == 0:
        return hdroller.dice.zero.ZeroDie(data, 0)
    elif ndim == 1:
        return hdroller.dice.single.SingleDie(data, 1)
    else:
        return hdroller.dice.multi.MultiDie(data, ndim)

def _make_data(arg, min_outcome=None, remove_zero_weights=True):
    """Creates a FrozenSortedWeights from the arguments."""
    if isinstance(arg, FrozenSortedWeights):
        data = arg
    elif min_outcome is not None:
        data = { min_outcome + i : weight for i, weight in enumerate(arg) }
    elif hasattr(arg, 'keys') and hasattr(arg, '__getitem__'):
        data = { k : arg[k] for k in arg.keys() }
    elif hasattr(arg, '__iter__'):
        data = { k : v for k, v in arg }
    else:
        # Treat arg as the only possible value.
        data = { arg : 1 }
    
    return FrozenSortedWeights(data, remove_zero_weights)
    

def _calc_ndim(data, ndim):
    """Verifies ndim if provided, or calculates it if not.
    
    Args:
        data: A FrozenSortedWeights.
        ndim: If provided, ndims will be set to this value.
        
    Returns:
        An appropriate ndim for a die.
        
    Raises:
        ValueError if ndim is provided but is not consistent with the data.
    """
    if ndim is not None:
        if ndim != 1:
            for outcome in data.keys():
                if len(outcome) != ndim:
                    raise ValueError('Outcomes not consistent with provided ndim.')
        return ndim
    
    if len(data) == 0:
        return None
    
    for outcome in data.keys():
        try:
            if ndim is None:
                ndim = len(outcome)
            elif len(outcome) != ndim:
                # The data has mixed dimensions.
                return 1
        except TypeError:
            # The data contains a scalar.
            return 1
    return ndim

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
    return die(d, ndim=ndim)
    
def from_sweights(outcomes, sweights, ndim=None):
    d = {}
    for i, outcome in enumerate(outcomes):
        if i < len(outcomes) - 1:
            weight = sweights[i] - sweights[i+1]
        else:
            weight = sweights[i]
        if weight > 0:
            d[outcome] = weight
    return die(d, ndim=ndim)

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
