__docformat__ = 'google'

import icepool

import math

from icepool.typing import Outcome, T
from typing import Iterable, Literal, Sequence, cast, overload


@overload
def lowest(iterable: 'Iterable[T | icepool.Die[T]]', /) -> 'icepool.Die[T]':
    ...


@overload
def lowest(arg0: 'T | icepool.Die[T]', arg1: 'T | icepool.Die[T]', /,
           *args: 'T | icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def lowest(arg0,
           /,
           *more_args: 'T | icepool.Die[T]',
           keep: int = 1,
           drop: int = 0) -> 'icepool.Die[T]':
    """The lowest outcome among the rolls, or the sum of some of the lowest.

    The outcomes should support addition and multiplication if `keep != 1`.

    Args:
        args: Dice or individual outcomes in a single iterable, or as two or
            more separate arguments. Similar to the built-in `min()`.
        keep: The number of lowest dice will be summed.
        drop: This number of lowest dice will be dropped before keeping dice
            to be summed.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0,) + more_args

    if keep < 0:
        raise ValueError(f'keep={keep} cannot be negative.')
    if drop < 0:
        raise ValueError(f'drop={drop} cannot be negative.')

    start = min(drop, len(args))
    stop = min(keep + drop, len(args))
    return _sum_slice(*args, start=start, stop=stop)


@overload
def highest(iterable: 'Iterable[T | icepool.Die[T]]', /) -> 'icepool.Die[T]':
    ...


@overload
def highest(arg0: 'T | icepool.Die[T]', arg1: 'T | icepool.Die[T]', /,
            *args: 'T | icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def highest(arg0,
            /,
            *more_args: 'T | icepool.Die[T]',
            keep: int = 1,
            drop: int = 0) -> 'icepool.Die[T]':
    """The highest outcome among the rolls, or the sum of some of the highest.

    The outcomes should support addition and multiplication if `keep != 1`.

    Args:
        args: Dice or individual outcomes in a single iterable, or as two or
            more separate arguments. Similar to the built-in `max()`.
        keep: The number of highest dice will be summed.
        drop: This number of highest dice will be dropped before keeping dice
            to be summed.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0,) + more_args

    if keep < 0:
        raise ValueError(f'keep={keep} cannot be negative.')
    if drop < 0:
        raise ValueError(f'drop={drop} cannot be negative.')

    start = len(args) - min(keep + drop, len(args))
    stop = len(args) - min(drop, len(args))
    return _sum_slice(*args, start=start, stop=stop)


@overload
def middle(iterable: 'Iterable[T | icepool.Die[T]]', /) -> 'icepool.Die[T]':
    ...


@overload
def middle(arg0: 'T | icepool.Die[T]', arg1: 'T | icepool.Die[T]', /,
           *args: 'T | icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def middle(arg0,
           /,
           *more_args: 'T | icepool.Die[T]',
           keep: int = 1,
           tie: Literal['error', 'high', 'low'] = 'error') -> 'icepool.Die[T]':
    """The middle of the outcomes among the rolls, or the sum of some of the middle.

    The outcomes should support addition and multiplication if `keep != 1`.

    Args:
        args: Dice or individual outcomes in a single iterable, or as two or
            more separate arguments.
        keep: The number of outcomes to sum.
        tie: What to do if `keep` is odd but the the number of args is even, or
            vice versa.
            * 'error' (default): Raises `IndexError`.
            * 'high': The higher outcome is taken.
            * 'low': The lower outcome is taken.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0,) + more_args
    # Expression evaluators are difficult to type.
    return icepool.Pool(args).middle(keep, tie=tie).sum()  # type: ignore


def _sum_slice(*args, start: int, stop: int) -> 'icepool.Die':
    """Common code for `lowest` and `highest`.

    Args:
        *args: The dice (not converted to `Die` yet).
        start, stop: The slice `start:stop` will be kept. These will be between
            0 and len(dice) inclusive.
    """

    dice: 'Sequence[icepool.Die]' = tuple(
        icepool.implicit_convert_to_die(arg) for arg in args)

    if len(dice) == 0:
        raise ValueError('At least one die must be provided.')

    if any(die.is_empty() for die in dice):
        return icepool.Die([])

    # The inputs should support addition.
    if start == stop:
        return sum(die.zero() for die in dice)  # type: ignore

    if start == 0 and stop == len(dice):
        return sum(dice)  # type: ignore

    if stop == 1:
        return _lowest_single(*dice)

    if start == len(dice) - 1:
        return _highest_single(*dice)

    # Use pool.
    # Expression evaluators are difficult to type.
    return icepool.Pool(dice)[start:stop].sum()  # type: ignore


def _lowest_single(*args: 'T | icepool.Die[T]') -> 'icepool.Die[T]':
    """Roll all the dice and take the lowest single one.

    The maximum outcome is equal to the least maximum outcome among all
    input dice.
    """
    dice = tuple(icepool.implicit_convert_to_die(arg) for arg in args)
    max_outcome = min(die.max_outcome() for die in dice)
    dice = tuple(die.clip(max_outcome=max_outcome) for die in dice)
    dice = icepool.align(*dice)
    quantities_ge = tuple(
        math.prod(t) for t in zip(*(die.quantities_ge() for die in dice)))
    return icepool.from_cumulative(dice[0].outcomes(),
                                   quantities_ge,
                                   reverse=True)


def _highest_single(*args: 'T | icepool.Die[T]') -> 'icepool.Die[T]':
    """Roll all the dice and take the highest single one.

    The minimum outcome is equal to the greatest minimum outcome among all
    input dice.
    """
    dice = tuple(icepool.implicit_convert_to_die(arg) for arg in args)
    min_outcome = max(die.min_outcome() for die in dice)
    dice = tuple(die.clip(min_outcome=min_outcome) for die in dice)
    dice = icepool.align(*dice)
    quantities_le = tuple(
        math.prod(t) for t in zip(*(die.quantities_le() for die in dice)))
    return icepool.from_cumulative(dice[0].outcomes(), quantities_le)
