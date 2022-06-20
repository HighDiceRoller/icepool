__docformat__ = 'google'

import icepool

import math


def lowest(*dice, keep: int = 1, drop: int = 0) -> 'icepool.Die':
    """The lowest outcome or sum of the lowest outcomes among the dice.

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
    return _lowest_highest(*dice, start=start, stop=stop)


def highest(*dice, keep: int = 1, drop: int = 0) -> 'icepool.Die':
    """The highest outcome or sum of the highest outcomes among the dice.

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
    return _lowest_highest(*dice, start=start, stop=stop)


def _lowest_highest(*dice, start: int, stop: int) -> 'icepool.Die':
    """Common code for `lowest` and `highest`.

    Args:
        *dice: The dice (not converted to `Die` yet).
        start, stop: The slice `start:stop` will be kept. These will be between
            0 and len(dice) inclusive.
    """

    dice = tuple(icepool.Die([die]) for die in dice)

    if len(dice) == 0:
        raise ValueError('At least one die must be provided.')

    if any(die.is_empty() for die in dice):
        return icepool.Die([])

    if start == stop:
        return sum(die.zero() for die in dice)  # type: ignore

    if start == 0 and stop == len(dice):
        return sum(dice)  # type: ignore

    if stop == 1:
        return _lowest_single(*dice)

    if start == len(dice) - 1:
        return _highest_single(*dice)

    # Use pool.
    return icepool.Pool(dice)[start:stop].sum()


def _lowest_single(*dice) -> 'icepool.Die':
    """Roll all the dice and take the lowest single.

    The maximum outcome is equal to the least maximum outcome among all
    input dice.
    """
    dice = tuple(icepool.Die([die]) for die in dice)
    max_outcome = min(die.max_outcome() for die in dice)
    dice = tuple(die.clip(max_outcome=max_outcome) for die in dice)
    dice = icepool.align(*dice)
    quantities_ge = tuple(
        math.prod(t) for t in zip(*(die.quantities_ge() for die in dice)))
    return icepool.from_cumulative_quantities(dice[0].outcomes(),
                                              quantities_ge,
                                              reverse=True)


def _highest_single(*dice) -> 'icepool.Die':
    """Roll all the dice and take the highest single.

    The minimum outcome is equal to the greatest minimum outcome among all
    input dice.
    """
    dice = tuple(icepool.Die([die]) for die in dice)
    min_outcome = max(die.min_outcome() for die in dice)
    dice = tuple(die.clip(min_outcome=min_outcome) for die in dice)
    dice = icepool.align(*dice)
    quantities_le = tuple(
        math.prod(t) for t in zip(*(die.quantities_le() for die in dice)))
    return icepool.from_cumulative_quantities(dice[0].outcomes(), quantities_le)
