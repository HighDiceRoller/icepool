__docformat__ = 'google'

import hdroller
from hdroller.collections import Weights
import hdroller.die.base
import hdroller.die.vector
import hdroller.die.scalar

from collections import defaultdict
import itertools
import math

def Die(*args, min_outcome=None, ndim=None):
    """ Factory for constructing a die.
    
    This is capitalized because it is the preferred way of getting a new instance,
    and so that you can use `from hdroller import Die` while leaving the name `die` free.
    The actual class of the result will be one of the subclasses of `BaseDie`.
    
    Don't confuse this with `hdroller.d()`:
    
    * `hdroller.Die(6)`: A die that always rolls the `int` 6.
    * `hdroller.d(6)`: A d6.
    
    Args:
        *args: This can be one of the following, with examples of how to create a d6 where applicable:
            * A single argument die, which will be returned itself.
                `d6 == Die(d6)`.
            * A single argument dict-like that maps outcomes to weights.
                This option will be taken in preference to treating the dict-like itself as an outcome
                even if the dict-like itself is hashable and comparable.
                `d6 == Die({1:1, 2:1, 3:1, 4:1, 5:1, 6:1})`.
            * A single argument sequence of weights, with `min_outcome` set to an `int`. 
                The outcomes will be `int`s starting at `min_outcome`.
                `d6 == Die([1, 1, 1, 1, 1, 1], min_outcome=1)`.
            * Zero or more arguments, each one denoting an outcome with weight 1 per appearance.
                The outcomes must be hashable and comparable.
                `d6 == Die(1, 2, 3, 4, 5, 6)`.
                Note that a single argument sequence will be treated as a single outcome; 
                for example, `Die((1, 2, 3, 4, 5, 6))` is a die that always rolls the tuple `(1, 2, 3, 4, 5, 6)`.
        min_outcome: Only used with a sequence of weights, as above.
        ndim: If set to `'scalar'`, the die will be forced to be scalar.
            If set to an `int`, the die will be forced to be vector with that number of dimensions.
            If omitted, this will be automatically detected.
            E.g. for `str` outcomes you may want to set `ndim='scalar'`, which will
            treat e.g. `'abc' as a single string rather than `('a', 'b', 'c')`.
    
    Raises:
        `ValueError` if `ndim` is set but is not consistent with `arg`.
            Also, `None` is not a valid outcome for a die.
    """
    data = _make_data(args, min_outcome)
        
    ndim = _calc_ndim(data, ndim)
    
    if isinstance(ndim, int):
        data = Weights({ tuple(k) : v for k, v in data.items() })
        return hdroller.die.vector.VectorDie(data, ndim)
    else:
        return hdroller.die.scalar.ScalarDie(data)

def _make_data(args, min_outcome=None):
    """ Creates a `Weights` from the arguments. """
    if len(args) == 1:
        arg = args[0]
        if isinstance(arg, hdroller.die.base.BaseDie):
            return arg._data
        elif isinstance(arg, Weights):
            return arg
        elif min_outcome is not None:
            return Weights({ min_outcome + i : weight for i, weight in enumerate(arg) })
        elif hasattr(arg, 'keys') and hasattr(arg, '__getitem__'):
            return Weights({ k : arg[k] for k in arg.keys() })

    # Default case: each argument becomes an outcome.
    data = defaultdict(int)
    for outcome in args:
        data[outcome] += 1
    
    return Weights(data)

def _calc_ndim(data, ndim):
    """Verifies `ndim` if provided and calculates it otherwise.
    
    Args:
        data: A `Weights`.
        ndim: If `None`, this will be determined from `data`.
            If provided, this will be verified.
        
    Returns:
        ndim: The number of dimensions, or `'scalar'` if the data is determined to be sclar.
        
    Raises:
        `ValueError` if `ndim` is provided but is not consistent with the data.
    """
    if len(data) == 0:
        return 'scalar'
    
    if ndim == 'scalar':
        return 'scalar'
    
    provided_ndim = ndim is not None
    
    for outcome in data.keys():
        if hasattr(outcome, '__len__'):
            if ndim is None:
                ndim = len(outcome)
            elif len(outcome) != ndim:
                # Found mixed dimension.
                if provided_ndim:
                    raise ValueError('Data does not match provided ndim.')
                else:
                    return 'scalar'
        else:
            if provided_ndim:
                raise ValueError('Provided ndim but found scalar value.')
            else:
                return 'scalar'
    
    return ndim

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
    return Die([1] * num_sides, min_outcome=1, ndim='scalar')
    
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
    elif isinstance(arg, hdroller.die.base.BaseDie):
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
    return Die({False : d - n, True : n}, ndim='scalar')

coin = bernoulli

def from_cweights(outcomes, cweights, ndim=None):
    """ Constructs a die from cumulative weights. """
    prev = 0
    d = {}
    for outcome, weight in zip(outcomes, cweights):
        d[outcome] = weight - prev
        prev = weight
    return Die(d, ndim=ndim)
    
def from_sweights(outcomes, sweights, ndim=None):
    """ Constructs a die from survival weights. """
    prev = 0
    d = {}
    for outcome, weight in zip(reversed(outcomes), reversed(tuple(sweights))):
        d[outcome] = weight - prev
        prev = weight
    return Die(d, ndim=ndim)

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

def mix(*dice, mix_weights=None, ndim=None, total_weight_method='lcm'):
    """ Constructs a die from a mixture of the input dice.
    
    This is equivalent to rolling a die and then choosing one of the input dice
    based on the resulting outcome rolled. See also `BaseDie.sub()`.
    
    Args:
        *dice: The dice to mix.
            These can be values castable to dice.
            Alternatively, values may be `hdroller.Reroll`,
            in which case that value and the corresponding mix weight is simply dropped.
        mix_weights: An iterable of one `int` weight per input die.
            If not provided, all dice are mixed uniformly.
        total_weight_method: How to determine the total weight of the result.
            From greatest to least:
            * 'prod': Product of all mixed dice, times the total of mixing weights.
                This is like rolling all of the possible dice, and then selecting a result based on the mixing weights.
            * 'lcm' (default): LCM of mixed dice, times the total of mixing weights.
                This is like rolling the mixing weights first, then selecting a mixed die to roll.
            * 'lcm_weighted': LCM of (mixed die * mixing weight for that die).
                This is like rolling the above, but the specific mixing weight rolled
                is used to help determine the result of the selected die.
    """
    if mix_weights is None:
        mix_weights = (1,) * len(dice)
    
    dice, mix_weights = zip(*((die, weight) for die, weight in zip(dice, mix_weights) if die is not hdroller.Reroll))
    
    dice = align(*dice, ndim=ndim)
    ndim = check_ndim(*dice)
        
    if total_weight_method == 'prod':
        weight_product = math.prod(die.total_weight() for die in dice)
    elif total_weight_method == 'lcm':
        weight_product = math.lcm(*(die.total_weight() for die in dice))
    elif total_weight_method == 'lcm_weighted':
        weight_product = math.lcm(*(die.total_weight() * w for die, w in zip(dice, mix_weights)))
    else:
        raise ValueError(f'Invalid total_weight_method {total_weight_method}.')
    
    data = defaultdict(int)
    for die, mix_weight in zip(dice, mix_weights):
        factor = mix_weight * weight_product // die.total_weight()
        for outcome, weight in zip(die.outcomes(), die.weights()):
            data[outcome] += weight * factor
    return Die(data, ndim=ndim)

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
    dice = [Die(die, ndim=ndim) for die in dice]
    check_ndim(*dice)
    outcomes = set(itertools.chain.from_iterable(die.outcomes() for die in dice))
    return tuple(die.set_outcomes(outcomes) for die in dice)

def align_range(*dice, ndim=None):
    """Pads all the dice with zero weights so that all have the same set of consecutive `int` outcomes. """
    dice = [Die(die, ndim=ndim) for die in dice]
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
    dice = [Die(die, ndim=ndim) for die in dice]
    data = defaultdict(int)
    for t in itertools.product(*(die.items() for die in dice)):
        outcomes, weights = zip(*t)
        data[func(*outcomes)] += math.prod(weights)
    
    return Die(data, ndim=ndim)
