__docformat__ = 'google'

import icepool

from collections import defaultdict
import itertools
import math


def standard(num_sides):
    """A standard die.

    Specifically, the outcomes are `int`s from `1` to `num_sides` inclusive,
    with weight 1 each.

    Don't confuse this with `icepool.Die()`:

    * `icepool.Die(6)`: A die that always rolls the integer 6.
    * `icepool.d(6)`: A d6.
    """
    if not isinstance(num_sides, int):
        raise TypeError('Argument to standard() must be an int.')
    elif num_sides < 1:
        raise ValueError('Standard die must have at least one side.')
    return icepool.Die(weights=[1] * num_sides, min_outcome=1)


def d(arg):
    """Converts the argument to a standard die if it is not already a die.

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
    elif isinstance(arg, icepool.Die):
        return arg
    else:
        raise TypeError('The argument to d() must be an int or a die.')


def __getattr__(key):
    """Implements the `dX` syntax for standard die with no parentheses.

    For example, `icepool.d6`.

    Note that this behavior can't be imported into the global scope, but the
    function `d()` can be.
    """
    if key[0] == 'd':
        try:
            return standard(int(key[1:]))
        except ValueError:
            pass
    raise AttributeError(key)


def bernoulli(n, d):
    """A die that rolls `True` with chance `n / d`, and `False` otherwise. """
    return icepool.Die({False: d - n, True: n})


coin = bernoulli


def from_cweights(outcomes, cweights):
    """Constructs a die from cumulative weights. """
    prev = 0
    d = {}
    for outcome, weight in zip(outcomes, cweights):
        d[outcome] = weight - prev
        prev = weight
    return icepool.Die(d)


def from_sweights(outcomes, sweights):
    """Constructs a die from survival weights. """
    prev = 0
    d = {}
    for outcome, weight in zip(reversed(outcomes), reversed(tuple(sweights))):
        d[outcome] = weight - prev
        prev = weight
    return icepool.Die(d)


def from_rv(rv, outcomes, denominator, **kwargs):
    """Constructs a die from a rv object (as `scipy.stats`).
    Args:
        rv: A rv object (as `scipy.stats`).
        outcomes: An iterable of `int`s or `float`s that will be the outcomes
            of the resulting die.
            If the distribution is discrete, outcomes must be `int`s.
        denominator: The denominator of the resulting die will be set to this.
        **kwargs: These will be provided to `rv.cdf()`.
    """
    if hasattr(rv, 'pdf'):
        # Continuous distributions use midpoints.
        midpoints = [(a + b) / 2 for a, b in zip(outcomes[:-1], outcomes[1:])]
        cdf = rv.cdf(midpoints, **kwargs)
        cweights = tuple(
            int(round(x * denominator)) for x in cdf) + (denominator,)
    else:
        cdf = rv.cdf(outcomes, **kwargs)
        cweights = tuple(int(round(x * denominator)) for x in cdf)
    return from_cweights(outcomes, cweights)


def align(*dice):
    """Pads dice with zero weights so that all have the same set of outcomes.

    Args:
        *dice: One die per argument.

    Returns:
        A tuple of aligned dice.
    """
    dice = [icepool.Die(die) for die in dice]
    outcomes = set(itertools.chain.from_iterable(
        die.outcomes() for die in dice))
    return tuple(die.set_outcomes(outcomes) for die in dice)


def align_range(*dice):
    """Pads dice with zero weights so that all have the same set of consecutive `int` outcomes.

    Args:
        *dice: One die per argument.

    Returns:
        A tuple of aligned dice.
    """
    dice = [icepool.Die(die) for die in dice]
    outcomes = tuple(
        range(icepool.min_outcome(*dice),
              icepool.max_outcome(*dice) + 1))
    return tuple(die.set_outcomes(outcomes) for die in dice)


def apply(func, *dice):
    """Applies `func(outcome_of_die_0, outcome_of_die_1, ...)` for all possible outcomes of the dice.

    This is flexible but not very efficient for large numbers of dice.
    In particular, for pools use `icepool.Pool` and `icepool.EvalPool` instead
    if possible.

    Args:
        func: A function that takes one argument per input die and returns an
            argument to `Die()`.

    Returns:
        A die constructed from the outputs of `func` and the product of the
        weights of the dice.
    """
    if len(dice) == 0:
        return icepool.Die()
    dice = [icepool.Die(die) for die in dice]
    final_outcomes = []
    final_weights = []
    data = defaultdict(int)
    for t in itertools.product(*(die.items() for die in dice)):
        outcomes, weights = zip(*t)
        final_outcome = func(*outcomes)
        final_weight = math.prod(weights)
        if final_outcome is not icepool.Reroll:
            final_outcomes.append(final_outcome)
            final_weights.append(final_weight)

    return icepool.Die(*final_outcomes, weights=final_weights)
