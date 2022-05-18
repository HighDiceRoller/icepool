__docformat__ = 'google'

import icepool

from collections import defaultdict
from functools import cache
import itertools
import math


@cache
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
    return icepool.Die(*range(1, num_sides + 1))


def d(arg):
    """Converts the argument to a standard die if it is not already a die.

    You may also use e.g. `icepool.d6` without the parentheses. However, this
    alternative behavior cannot be imported into the global scope:

    ```
    import icepool
    from icepool import d
    d(6)                    # ok
    icepool.d6              # ok
    d6                      # not ok
    from icepool import d6  # ok
    ```

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


def min_outcome(*dice):
    """Returns the minimum possible outcome among the dice. """
    return min(die.outcomes()[0] for die in dice)


def max_outcome(*dice):
    """Returns the maximum possible outcome among the dice. """
    return max(die.outcomes()[-1] for die in dice)


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


def reduce(func, dice, *, initial=None):
    """Applies a function of two arguments cumulatively to a sequence of dice.

    Analogous to
    [`functools.reduce()`](https://docs.python.org/3/library/functools.html#functools.reduce).

    The function is applied non-elementwise to tuple outcomes.

    Args:
        func: The function to apply. The function should take two arguments,
            which are an outcome from each of two dice.
        dice: A sequence of dice to apply the function to, from left to right.
        initial: If provided, this will be placed at the front of the sequence
            of dice.
    """
    # Conversion to dice is not necessary since apply() takes care of that.
    iter_dice = iter(dice)
    if initial is not None:
        result = initial
    else:
        result = next(iter_dice)
    for die in iter_dice:
        result = apply(func, result, die)
    return result


def accumulate(func, dice, *, initial=None):
    """Applies a function of two arguments cumulatively to a sequence of dice, yielding each result in turn.

    Analogous to
    [`itertools.accumulate()`](https://docs.python.org/3/library/itertools.html#itertools.accumulate)
    , though with no default function and
    the same parameter order as `reduce()`.

    The number of results is equal to the number of elements of `dice`, with
    one additional element if `initial` is provided.

    The function is applied non-elementwise to tuple outcomes.

    Args:
        func: The function to apply. The function should take two arguments,
            which are an outcome from each of two dice.
        dice: A sequence of dice to apply the function to, from left to right.
        initial: If provided, this will be placed at the front of the sequence
            of dice.
    """
    # Conversion to dice is not necessary since apply() takes care of that.
    iter_dice = iter(dice)
    if initial is not None:
        result = initial
    else:
        try:
            result = next(iter_dice)
        except StopIteration:
            return
    yield result
    for die in iter_dice:
        result = apply(func, result, die)
        yield result


def apply(func, *dice):
    """Applies `func(outcome_of_die_0, outcome_of_die_1, ...)` for all possible outcomes of the dice.

    Example: `apply(lambda a, b: a + b, d6, d6)` is the same as d6 + d6.

    `apply()` is flexible but not very efficient for more than two dice.
    Instead of using a large number of arguments:
    * If the problem is easy to solve by considering one additional die at a
        time, try using `reduce()` instead.
    * If the problem is easy to solve by considering how many dice rolled each
        outcome, one outcome at a time, try using
        `icepool.Pool` and `icepool.EvalPool`.

    Args:
        func: A function that takes one argument per input die and returns an
            argument to `Die()`.
        *dice: Any number of dice (or objects convertible to dice).
            `func` will be called with all possible joint outcomes of `dice`,
            with one argument per die.

    Returns:
        A die constructed from the outputs of `func` and the product of the
        weights of the dice.
    """
    if len(dice) == 0:
        return icepool.Die()
    dice = [icepool.Die(die) for die in dice]
    final_outcomes = []
    final_weights = []
    for t in itertools.product(*(die.items() for die in dice)):
        outcomes, weights = zip(*t)
        final_outcome = func(*outcomes)
        final_weight = math.prod(weights)
        if final_outcome is not icepool.Reroll:
            final_outcomes.append(final_outcome)
            final_weights.append(final_weight)

    return icepool.Die(*final_outcomes, weights=final_weights)
