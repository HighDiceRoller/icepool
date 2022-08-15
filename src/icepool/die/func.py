__docformat__ = 'google'

import icepool

from collections import defaultdict
from functools import cache
import itertools
import math

from typing import Any, Callable, Generator, Sequence


@cache
def standard(sides: int, /) -> 'icepool.Die':
    """A standard die.

    Specifically, the outcomes are `int`s from `1` to `sides` inclusive,
    with quantity 1 each.

    Don't confuse this with `icepool.Die()`:

    * `icepool.Die([6])`: A `Die` that always rolls the integer 6.
    * `icepool.d(6)`: A d6.
    """
    if not isinstance(sides, int):
        raise TypeError('Argument to standard() must be an int.')
    elif sides < 1:
        raise ValueError('Standard die must have at least one side.')
    return icepool.Die(range(1, sides + 1))


d = standard


def __getattr__(key: str):
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


def bernoulli(n: int, d: int, /) -> 'icepool.Die':
    """A `Die` that rolls `True` with probability `n / d`, and `False` otherwise.

    If `n == 0` or `n == d` the result will have only one outcome.
    """
    data = {}
    if n != d:
        data[False] = d - n
    if n != 0:
        data[True] = n
    return icepool.Die(data)


coin = bernoulli


def from_cumulative_quantities(outcomes: Sequence,
                               cumulative_quantities: Sequence[int],
                               *,
                               reverse: bool = False) -> 'icepool.Die':
    """Constructs a `Die` from a sequence of cumulative quantities.

    Args:
        outcomes: The outcomes of the resulting die. Sorted order is recommended
            but not necessary.
        cumulative_quantities: The cumulative quantities (inclusive) of the
            outcomes in the order they are given to this function.
        reverse: Iff true, both of the arguments will be reversed. This allows
            e.g. constructing using a survival distribution.
    """

    prev = 0
    d = {}
    for outcome, quantity in zip((reversed(outcomes) if reverse else outcomes),
                                 (reversed(cumulative_quantities)
                                  if reverse else cumulative_quantities)):
        d[outcome] = quantity - prev
        prev = quantity
    return icepool.Die(d)


def from_rv(rv, outcomes: Sequence[int | float], denominator: int, **kwargs):
    """Constructs a `Die` from a rv object (as `scipy.stats`).
    Args:
        rv: A rv object (as `scipy.stats`).
        outcomes: An iterable of `int`s or `float`s that will be the outcomes
            of the resulting `Die`.
            If the distribution is discrete, outcomes must be `int`s.
        denominator: The denominator of the resulting `Die` will be set to this.
        **kwargs: These will be provided to `rv.cdf()`.
    """
    if hasattr(rv, 'pdf'):
        # Continuous distributions use midpoints.
        midpoints = [(a + b) / 2 for a, b in zip(outcomes[:-1], outcomes[1:])]
        cdf = rv.cdf(midpoints, **kwargs)
        quantities_le = tuple(
            int(round(x * denominator)) for x in cdf) + (denominator,)
    else:
        cdf = rv.cdf(outcomes, **kwargs)
        quantities_le = tuple(int(round(x * denominator)) for x in cdf)
    return from_cumulative_quantities(outcomes, quantities_le)


def min_outcome(*dice):
    """The minimum outcome among the dice. """
    dice = [icepool.Die([die]) for die in dice]
    return min(die.outcomes()[0] for die in dice)


def max_outcome(*dice):
    """The maximum outcome among the dice. """
    dice = [icepool.Die([die]) for die in dice]
    return max(die.outcomes()[-1] for die in dice)


def align(*dice) -> tuple['icepool.Die', ...]:
    """Pads dice with zero quantities so that all have the same set of outcomes.

    Args:
        *dice: One `Die` per argument.

    Returns:
        A tuple of aligned dice.
    """
    dice = tuple(icepool.Die([die]) for die in dice)
    outcomes = set(itertools.chain.from_iterable(
        die.outcomes() for die in dice))
    return tuple(die.set_outcomes(outcomes) for die in dice)


def align_range(*dice) -> tuple['icepool.Die', ...]:
    """Pads dice with zero quantities so that all have the same set of consecutive `int` outcomes.

    Args:
        *dice: One `Die` per argument.

    Returns:
        A tuple of aligned dice.
    """
    dice = tuple(icepool.Die([die]) for die in dice)
    outcomes = tuple(
        range(icepool.min_outcome(*dice),
              icepool.max_outcome(*dice) + 1))
    return tuple(die.set_outcomes(outcomes) for die in dice)


def reduce(func: Callable[[Any, Any], Any],
           dice,
           *,
           initial=None) -> 'icepool.Die':
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
        result = icepool.Die([initial])
    else:
        result = next(iter_dice)
    for die in iter_dice:
        result = apply(func, result, die)
    return result


def accumulate(func: Callable[[Any, Any], Any],
               dice,
               *,
               initial=None) -> Generator['icepool.Die', None, None]:
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
        result = icepool.Die([initial])
    else:
        try:
            result = next(iter_dice)
        except StopIteration:
            return
    yield result
    for die in iter_dice:
        result = apply(func, result, die)
        yield result


def apply(func: Callable, *dice) -> 'icepool.Die':
    """Applies `func(outcome_of_die_0, outcome_of_die_1, ...)` for all outcomes of the dice.

    Example: `apply(lambda a, b: a + b, d6, d6)` is the same as d6 + d6.

    `apply()` is flexible but not very efficient for more than two dice.
    Instead of using more than two arguments:

    * If the problem is easy to solve by considering one additional `Die` at a
        time, try using `reduce()` instead.
    * If the problem is easy to solve by considering how many dice rolled each
        outcome, one outcome at a time, try using
        `icepool.Pool` and `icepool.OutcomeCountEvaluator`.
    * If the order in which the dice are rolled is not important, you can use
        `apply_sorted()`. This is less efficient than either of the above two,
        but is still more efficient than `apply()`.

    Args:
        func: A function that takes one argument per input `Die` and returns an
            argument to `Die()`.
        *dice: Any number of dice (or objects convertible to dice).
            `func` will be called with all joint outcomes of `dice`, with one
            argument per `Die`.

    Returns:
        A `Die` constructed from the outputs of `func` and the product of the
        quantities of the dice.
    """
    if not callable(func):
        raise TypeError(
            'The first argument must be callable. Did you forget to provide a function?'
        )
    if len(dice) == 0:
        return icepool.Die([func()])
    dice = tuple(icepool.Die([die]) for die in dice)
    final_outcomes = []
    final_quantities = []
    for t in itertools.product(*(die.items() for die in dice)):
        outcomes, quantities = zip(*t)
        final_outcome = func(*outcomes)
        final_quantity = math.prod(quantities)
        if final_outcome is not icepool.Reroll:
            final_outcomes.append(final_outcome)
            final_quantities.append(final_quantity)

    return icepool.Die(final_outcomes, final_quantities)


class apply_sorted():
    """This is really a function implemented as a class.

    See the "constructor" for details.
    """

    def __new__(cls, func: Callable, *dice) -> 'icepool.Die':  # type: ignore
        """Applies `func(lowest_outcome, next_lowest_outcome...)` for all sorted joint outcomes of the dice.

        Not actually a constructor.

        This is more efficient than `apply()` but still not very efficient.
        Use `OutcomeCountEvaluator` instead if at all possible.

        You can use `apply_sorted[]` to only see outcomes at particular sorted indexes.
        For example, `apply_sorted[-2:](func, *dice)` would give the two highest
        outcomes to `func()`. This is more efficient than selecting outcomes inside
        `func`.

        Args:
            func: A function that takes one argument per input `Die` and returns an
                argument to `Die()`.
            *dice: Any number of dice (or objects convertible to dice).
                `func` will be called with all sorted joint outcomes of `dice`,
                with one argument per die. All outcomes must be totally orderable.

        Returns:
            A `Die` constructed from the outputs of `func` and the weight of rolling
            the corresponding sorted outcomes.
        """
        if not callable(func):
            raise TypeError(
                'The first argument must be callable. Did you forget to provide a function?'
            )
        pool = icepool.Pool(dice)
        return icepool.expand_evaluator(pool).sub(func, star=1)

    def __class_getitem__(cls,
                          sorted_roll_counts: int | slice | tuple[int, ...],
                          /) -> Callable[..., 'icepool.Die']:
        """Implements `[]` syntax for `apply_sorted`."""
        if isinstance(sorted_roll_counts, int):

            def result(func: Callable, *dice) -> 'icepool.Die':
                if not callable(func):
                    raise TypeError(
                        'The first argument must be callable. Did you forget to provide a function?'
                    )
                die = icepool.Pool(dice)[sorted_roll_counts]
                return die.sub(func)
        else:

            def result(func: Callable, *dice) -> 'icepool.Die':
                if not callable(func):
                    raise TypeError(
                        'The first argument must be callable. Did you forget to provide a function?'
                    )
                pool = icepool.Pool(dice)[sorted_roll_counts]
                return icepool.expand_evaluator(pool).sub(func, star=1)

        return result
