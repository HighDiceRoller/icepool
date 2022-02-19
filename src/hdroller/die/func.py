__docformat__ = 'google'

import hdroller

from collections import defaultdict
import itertools
import math

def standard(num_sides):
    """ A standard die.
    
    Specifically, the outcomes are `int`s from `1` to `num_sides` inclusive, with weight 1 each. 
    
    Don't confuse this with `hdroller.Die()`:
    
    * `hdroller.Die(6)`: A die that always rolls the integer 6.
    * `hdroller.d(6)`: A d6.
    """
    if not isinstance(num_sides, int):
        raise TypeError('Argument to standard() must be an int.')
    elif num_sides < 1:
        raise ValueError('Standard die must have at least one side.')
    return hdroller.Die(weights=[1] * num_sides, min_outcome=1, ndim='scalar')
    
def d(arg):
    """ Converts the argument to a standard die if it is not already a die.
    
    Args:
        arg: Either:
            * An `int`, which produces a standard die.
            * A die, which is returned itself.
    
    Returns:
        A die.
        
    Raises:
        `TypeError` if the argument is not an `int` or a die.
    """
    if isinstance(arg, int):
        return standard(arg)
    elif isinstance(arg, hdroller.BaseDie):
        return arg
    else:
        raise TypeError('The argument to d() must be an int or a die.')

def __getattr__(key):
    """ Implements the `dX` syntax for standard die with no parentheses, e.g. `hdroller.d6`. """
    if key[0] == 'd':
        try:
            return standard(int(key[1:]))
        except ValueError:
            pass
    raise AttributeError(key)

def bernoulli(n, d):
    """ A die that rolls `True` with chance `n / d`, and `False` otherwise. """
    return hdroller.Die({False : d - n, True : n}, ndim='scalar')

coin = bernoulli

def from_cweights(outcomes, cweights, ndim=None):
    """ Constructs a die from cumulative weights. """
    prev = 0
    d = {}
    for outcome, weight in zip(outcomes, cweights):
        d[outcome] = weight - prev
        prev = weight
    return hdroller.Die(d, ndim=ndim)
    
def from_sweights(outcomes, sweights, ndim=None):
    """ Constructs a die from survival weights. """
    prev = 0
    d = {}
    for outcome, weight in zip(reversed(outcomes), reversed(tuple(sweights))):
        d[outcome] = weight - prev
        prev = weight
    return hdroller.Die(d, ndim=ndim)

def from_rv(rv, outcomes, denominator, **kwargs):
    """ Constructs a die from a rv object (as `scipy.stats`).
    Args:
        rv: A rv object (as `scipy.stats`).
        outcomes: An iterable of `int`s or `float`s that will be the outcomes of the resulting die.
            If the distribution is discrete, outcomes must be `int`s.
        denominator: The total weight of the resulting die will be set to this.
        **kwargs: These will be provided to `rv.cdf()`.
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

def align(*dice, ndim=None):
    """Pads all the dice with zero weights so that all have the same set of outcomes.
    
    Args:
        *dice: Multiple dice or a single iterable of dice.
        ndim: The number of dimensions of the result.
    
    Returns:
        A tuple of aligned dice.
    
    Raises:
        `ValueError` if the dice are of mixed ndims.
    """
    dice = [hdroller.Die(die, ndim=ndim) for die in dice]
    check_ndim(*dice)
    outcomes = set(itertools.chain.from_iterable(die.outcomes() for die in dice))
    return tuple(die.set_outcomes(outcomes) for die in dice)

def align_range(*dice, ndim=None):
    """Pads all the dice with zero weights so that all have the same set of consecutive `int` outcomes. """
    dice = [hdroller.Die(die, ndim=ndim) for die in dice]
    check_ndim(*dice)
    outcomes = tuple(range(hdroller.min_outcome(*dice), hdroller.max_outcome(*dice) + 1))
    return tuple(die.set_outcomes(outcomes) for die in dice)

def check_ndim(*dice):
    """ Checks that `ndim` matches between the dice, and returns it. 
    
    Empty dice are not required to match.
    
    Args:
        *dice: The dice to be checked.
    
    Returns:
        The common `ndim` of the dice.
    
    Raises:
        ValueError if no dice were provided, or a mismatch in `ndim` is found.
    """
    if len(dice) == 0:
        raise ValueError('No dice were provided.')
    
    ndim = None
    for die in dice:
        if die.is_empty():
            continue
        if ndim is None:
            ndim = die.ndim()
        elif die.ndim() != ndim:
            raise ValueError('Dice have mismatched ndim.')
    return ndim

def apply(func, *dice, ndim=None):
    """ Applies `func(outcome_of_die_0, outcome_of_die_1, ...)` for all possible outcomes of the dice.
    
    This is flexible but not very efficient for large numbers of dice.
    In particular, for pools use `hdroller.Pool` and `hdroller.EvalPool` instead if possible.
    
    Args:
        func: A function that takes one argument per input die and returns a new outcome.
        ndim: If supplied, the result will have this many dimensions.
    
    Returns:
        A die constructed from the outputs of `func` and the product of the weights of the dice.
    """
    dice = [hdroller.Die(die, ndim=ndim) for die in dice]
    data = defaultdict(int)
    for t in itertools.product(*(die.items() for die in dice)):
        outcomes, weights = zip(*t)
        data[func(*outcomes)] += math.prod(weights)
    
    return hdroller.Die(data, ndim=ndim)
