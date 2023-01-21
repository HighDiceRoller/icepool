__docformat__ = 'google'

import icepool

import math

from icepool.typing import Outcome, T_contra
from typing import Literal, cast


def lowest(*dice, keep: int = 1, drop: int = 0) -> 'icepool.Die':
    """The lowest outcome among the rolls, or the sum of some of the lowest.

    The outcomes should support addition and multiplication if `keep != 1`.

    Args:
        *dice: The dice to be considered. At least one `Die` must be provided.
        keep: The number of lowest dice will be summed.
        drop: This number of lowest dice will be dropped before keeping dice
            to be summed.
    """
    if keep < 0:
        raise ValueError(f'keep={keep} cannot be negative.')
    if drop < 0:
        raise ValueError(f'drop={drop} cannot be negative.')

    start = min(drop, len(dice))
    stop = min(keep + drop, len(dice))
    return _sum_slice(*dice, start=start, stop=stop)


def highest(*dice, keep: int = 1, drop: int = 0) -> 'icepool.Die':
    """The highest outcome among the rolls, or the sum of some of the highest.

    The outcomes should support addition and multiplication if `keep != 1`.

    Args:
        *dice: The dice to be considered. At least one `Die` must be provided.
        keep: The number of highest dice will be summed.
        drop: This number of highest dice will be dropped before keeping dice
            to be summed.
    """
    if keep < 0:
        raise ValueError(f'keep={keep} cannot be negative.')
    if drop < 0:
        raise ValueError(f'drop={drop} cannot be negative.')

    start = len(dice) - min(keep + drop, len(dice))
    stop = len(dice) - min(drop, len(dice))
    return _sum_slice(*dice, start=start, stop=stop)


def middle(*dice,
           keep: int = 1,
           tie: Literal['error', 'high', 'low'] = 'error') -> 'icepool.Die':
    """The middle of the outcomes among the rolls, or the sum of some of the middle.

    The outcomes should support addition and multiplication if `keep != 1`.

    Args:
        keep: The number of outcomes to sum. If this is greater than the
            current keep_size, all are kept.
        tie: What to do if `keep` is odd but the current keep_size
            is even, or vice versa.
            * 'error' (default): Raises `IndexError`.
            * 'high': The higher outcome is taken.
            * 'low': The lower outcome is taken.
    """
    # Expression evaluators are difficult to type.
    return icepool.Pool(dice).middle(keep, tie=tie).sum()  # type: ignore


def _sum_slice(*dice, start: int, stop: int) -> 'icepool.Die':
    """Common code for `lowest` and `highest`.

    Args:
        *dice: The dice (not converted to `Die` yet).
        start, stop: The slice `start:stop` will be kept. These will be between
            0 and len(dice) inclusive.
    """

    dice = tuple(icepool.implicit_convert_to_die(die) for die in dice)

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


def _lowest_single(
        *args: 'T_contra | icepool.Die[T_contra]') -> 'icepool.Die[T_contra]':
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
    return icepool.from_cumulative_quantities(dice[0].outcomes(),
                                              quantities_ge,
                                              reverse=True)


def _highest_single(
        *args: 'T_contra | icepool.Die[T_contra]') -> 'icepool.Die[T_contra]':
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
    return icepool.from_cumulative_quantities(dice[0].outcomes(), quantities_le)
