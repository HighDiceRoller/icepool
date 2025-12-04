"""Free functions."""

__docformat__ = 'google'

import icepool
from icepool.math import weighted_lcm
from icepool.typing import T

from fractions import Fraction
from functools import cache
import itertools
import math

from typing import Iterable, Iterator, Sequence, cast, overload


@cache
def d(sides: int, /) -> 'icepool.Die[int]':
    """A standard die, uniformly distributed from `1` to `sides` inclusive.

    Don't confuse this with `icepool.Die()`:

    * `icepool.Die([6])`: A `Die` that always rolls the integer 6.
    * `icepool.d(6)`: A d6.

    You can also import individual standard dice from the `icepool` module, e.g.
    `from icepool import d6`.
    """
    if not isinstance(sides, int):
        raise TypeError('sides must be an int.')
    elif sides < 1:
        raise ValueError('sides must be at least 1.')
    return icepool.Die(range(1, sides + 1))


@cache
def z(sides: int, /) -> 'icepool.Die[int]':
    """A die uniformly distributed from `0` to `sides - 1` inclusive.
    
    Equal to d(sides) - 1.
    """
    if not isinstance(sides, int):
        raise TypeError('sides must be an int.')
    elif sides < 1:
        raise ValueError('sides must be at least 1.')
    return icepool.Die(range(0, sides))


def __getattr__(key: str) -> 'icepool.Die[int]':
    """Implements the `dX` syntax for standard die with no parentheses.

    For example, `icepool.d6`.

    Note that this behavior can't be imported into the global scope, but the
    function `d()` can be.

    Similar for `zX` and `z()`.
    """
    if key[0] == 'd':
        try:
            return d(int(key[1:]))
        except ValueError:
            pass
    elif key[0] == 'z':
        try:
            return z(int(key[1:]))
        except ValueError:
            pass
    raise AttributeError(key)


def coin(n: int | float | Fraction,
         d: int = 1,
         /,
         *,
         max_denominator: int | None = None) -> 'icepool.Die[bool]':
    """A `Die` that rolls `True` with probability `n / d`, and `False` otherwise.

    If `n <= 0` or `n >= d` the result will have only one outcome.

    Args:
        n: An int numerator, or a non-integer probability.
        d: An int denominator. Should not be provided if the first argument is
            not an int.
    """
    if not isinstance(n, int):
        if d != 1:
            raise ValueError(
                'If a non-int numerator is provided, a denominator must not be provided.'
            )
        fraction = Fraction(n)
        if max_denominator is not None:
            fraction = fraction.limit_denominator(max_denominator)
        n = fraction.numerator
        d = fraction.denominator
    data = {}
    if n < d:
        data[False] = min(d - n, d)
    if n > 0:
        data[True] = min(n, d)

    return icepool.Die(data)


def stochastic_round(x,
                     /,
                     *,
                     max_denominator: int | None = None) -> 'icepool.Die[int]':
    """Randomly rounds a value up or down to the nearest integer according to the two distances.
        
    Specificially, rounds `x` up with probability `x - floor(x)` and down
    otherwise, producing a `Die` with up to two outcomes.

    Args:
        max_denominator: If provided, each rounding will be performed
            using `fractions.Fraction.limit_denominator(max_denominator)`.
            Otherwise, the rounding will be performed without
            `limit_denominator`.
    """
    integer_part = math.floor(x)
    fractional_part = x - integer_part
    return integer_part + coin(fractional_part,
                               max_denominator=max_denominator)


def one_hot(sides: int, /) -> 'icepool.Die[tuple[bool, ...]]':
    """A `Die` with `Vector` outcomes with one element set to `True` uniformly at random and the rest `False`.

    This is an easy (if somewhat expensive) way of representing how many dice
    in a pool rolled each number. For example, the outcomes of `10 @ one_hot(6)`
    are the `(ones, twos, threes, fours, fives, sixes)` rolled in 10d6.
    """
    data = []
    for i in range(sides):
        outcome = [False] * sides
        outcome[i] = True
        data.append(icepool.Vector(outcome))
    return icepool.Die(data)


def from_cumulative(outcomes: Sequence[T],
                    cumulative: 'Sequence[int] | Sequence[icepool.Die[bool]]',
                    *,
                    reverse: bool = False) -> 'icepool.Die[T]':
    """Constructs a `Die` from a sequence of cumulative values.

    Args:
        outcomes: The outcomes of the resulting die. Sorted order is recommended
            but not necessary.
        cumulative: The cumulative values (inclusive) of the outcomes in the
            order they are given to this function. These may be:
            * `int` cumulative quantities.
            * Dice representing the cumulative distribution at that point.
        reverse: Iff true, both of the arguments will be reversed. This allows
            e.g. constructing using a survival distribution.
    """
    if len(outcomes) == 0:
        return icepool.Die({})

    if reverse:
        outcomes = list(reversed(outcomes))
        cumulative = list(reversed(cumulative))  # type: ignore

    prev = 0
    d = {}

    if isinstance(cumulative[0], icepool.Die):
        cumulative = harmonize_denominators(cumulative)
        for outcome, die in zip(outcomes, cumulative):
            d[outcome] = die.quantity('!=', False) - prev
            prev = die.quantity('!=', False)
    elif isinstance(cumulative[0], int):
        cumulative = cast(Sequence[int], cumulative)
        for outcome, quantity in zip(outcomes, cumulative):
            d[outcome] = quantity - prev
            prev = quantity
    else:
        raise TypeError(
            f'Unsupported type {type(cumulative)} for cumulative values.')

    return icepool.Die(d)


@overload
def from_rv(rv, outcomes: Sequence[int], denominator: int,
            **kwargs) -> 'icepool.Die[int]':
    ...


@overload
def from_rv(rv, outcomes: Sequence[float], denominator: int,
            **kwargs) -> 'icepool.Die[float]':
    ...


def from_rv(rv, outcomes: Sequence[int] | Sequence[float], denominator: int,
            **kwargs) -> 'icepool.Die[int] | icepool.Die[float]':
    """Constructs a `Die` from a rv object (as `scipy.stats`).

    This is done using the CDF.

    Args:
        rv: A rv object (as `scipy.stats`).
        outcomes: An iterable of `int`s or `float`s that will be the outcomes
            of the resulting `Die`.
            If the distribution is discrete, outcomes must be `int`s.
            Some outcomes may be omitted if their probability is too small
            compared to the denominator.
        denominator: The denominator of the resulting `Die` will be set to this.
        **kwargs: These will be forwarded to `rv.cdf()`.
    """
    if hasattr(rv, 'pdf'):
        # Continuous distributions use midpoints.
        midpoints = [(a + b) / 2 for a, b in zip(outcomes[:-1], outcomes[1:])]
        cdf = rv.cdf(midpoints, **kwargs)
        quantities_le = tuple(int(round(x * denominator))
                              for x in cdf) + (denominator, )
    else:
        cdf = rv.cdf(outcomes, **kwargs)
        quantities_le = tuple(int(round(x * denominator)) for x in cdf)
    return from_cumulative(outcomes, quantities_le)


def _iter_outcomes(
        *args: 'Iterable[T | icepool.Population[T]] | T') -> Iterator[T]:
    if len(args) == 1:
        iter_args = cast('Iterable[T | icepool.Population[T]]', args[0])
    else:
        iter_args = cast('Iterable[T | icepool.Population[T]]', args)
    for arg in iter_args:
        if isinstance(arg, icepool.Population):
            yield from arg
        else:
            yield arg


@overload
def pointwise_max(
    arg0: 'Iterable[icepool.Die[T]]',
    /,
) -> 'icepool.Die[T]':
    ...


@overload
def pointwise_max(arg0: 'icepool.Die[T]', arg1: 'icepool.Die[T]', /, *args:
                  'icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def pointwise_max(arg0, /, *more_args: 'icepool.Die[T]') -> 'icepool.Die[T]':
    """Selects the highest chance of rolling >= each outcome among the arguments.

    Naming not finalized.

    Specifically, for each outcome, the chance of the result rolling >= to that 
    outcome is the same as the highest chance of rolling >= that outcome among
    the arguments.

    Equivalently, any quantile in the result is the highest of that quantile
    among the arguments.

    This is useful for selecting from several possible moves where you are
    trying to get >= a threshold that is known but could change depending on the
    situation.
    
    Args:
        dice: Either an iterable of dice, or two or more dice as separate
            arguments.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0, ) + more_args
    args = harmonize_denominators(args)
    outcomes = sorted_union(*args)
    cumulative = [
        min(die.quantity('<=', outcome) for die in args)
        for outcome in outcomes
    ]
    return from_cumulative(outcomes, cumulative)


@overload
def pointwise_min(
    arg0: 'Iterable[icepool.Die[T]]',
    /,
) -> 'icepool.Die[T]':
    ...


@overload
def pointwise_min(arg0: 'icepool.Die[T]', arg1: 'icepool.Die[T]', /, *args:
                  'icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def pointwise_min(arg0, /, *more_args: 'icepool.Die[T]') -> 'icepool.Die[T]':
    """Selects the highest chance of rolling <= each outcome among the arguments.

    Naming not finalized.
    
    Specifically, for each outcome, the chance of the result rolling <= to that 
    outcome is the same as the highest chance of rolling <= that outcome among
    the arguments.

    Equivalently, any quantile in the result is the lowest of that quantile
    among the arguments.

    This is useful for selecting from several possible moves where you are
    trying to get <= a threshold that is known but could change depending on the
    situation.
    
    Args:
        dice: Either an iterable of dice, or two or more dice as separate
            arguments.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0, ) + more_args
    args = harmonize_denominators(args)
    outcomes = sorted_union(*args)
    cumulative = [
        max(die.quantity('<=', outcome) for die in args)
        for outcome in outcomes
    ]
    return from_cumulative(outcomes, cumulative)


@overload
def min_outcome(arg: 'Iterable[T | icepool.Population[T]]', /) -> T:
    ...


@overload
def min_outcome(*args: 'T | icepool.Population[T]') -> T:
    ...


def min_outcome(*args: 'Iterable[T | icepool.Population[T]] | T') -> T:
    """The minimum possible outcome among the populations.
    
    Args:
        Populations or single outcomes. Alternatively, a single iterable argument of such.
    """
    return min(_iter_outcomes(*args))


@overload
def max_outcome(arg: 'Iterable[T | icepool.Population[T]]', /) -> T:
    ...


@overload
def max_outcome(*args: 'T | icepool.Population[T]') -> T:
    ...


def max_outcome(*args: 'Iterable[T | icepool.Population[T]] | T') -> T:
    """The maximum possible outcome among the populations.
    
    Args:
        Populations or single outcomes. Alternatively, a single iterable argument of such.
    """
    return max(_iter_outcomes(*args))


def consecutive(*args: Iterable[int]) -> Sequence[int]:
    """A minimal sequence of consecutive ints covering the argument sets."""
    start = min((x for x in itertools.chain(*args)), default=None)
    if start is None:
        return ()
    stop = max(x for x in itertools.chain(*args))
    return tuple(range(start, stop + 1))


def sorted_union(*args: Iterable[T]) -> tuple[T, ...]:
    """Merge sets into a sorted sequence."""
    if not args:
        return ()
    return tuple(sorted(set.union(*(set(arg) for arg in args))))


def harmonize_denominators(dice: 'Sequence[T | icepool.Die[T]]',
                           weights: Sequence[int] | None = None,
                           /) -> tuple['icepool.Die[T]', ...]:
    """Scale the quantities of the dice so that the denominators are proportional to given weights.

    Args:
        dice: Any number of dice or single outcomes convertible to dice.
        weights: The target relative denominators of the dice. If not provided,
            all dice will be scaled to the same denominator, the same as
            `weights = [1] * len(dice)`.

    Returns:
        A tuple of dice with the adjusted denominators.
    """
    if weights is None:
        weights = [1] * len(dice)
    converted_dice = [icepool.implicit_convert_to_die(die) for die in dice]
    scale_factors = weighted_lcm([d.denominator() for d in converted_dice],
                                 weights)
    return tuple(
        die.multiply_quantities(scale_factor)
        for die, scale_factor in zip(converted_dice, scale_factors))
