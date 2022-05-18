__docformat__ = 'google'

import icepool

import math


def lowest(*dice, num_keep=1, num_drop=0):
    """The lowest outcome or sum of the lowest outcomes among the dice.

    Args:
        *dice: The dice to be considered.
        num_keep: The number of lowest dice will be summed.
        num_drop: This number of lowest dice will be dropped before keeping dice
            to be summed.
    """
    if num_keep < 0:
        raise ValueError(f'num_drop={num_keep} cannot be negative.')
    if num_drop < 0:
        raise ValueError(f'num_drop={num_drop} cannot be negative.')

    if len(dice) == 0:
        return icepool.Die()
    dice = [icepool.Die(die) for die in dice]
    if num_keep == 0 or num_drop >= len(dice):
        return sum(die.zero() for die in dice)

    if num_keep == 1 and num_drop == 0:
        return _lowest_single(*dice)
    elif num_keep >= len(dice) and num_drop == 0:
        return sum(dice)

    # Try to forumulate as a pool problem.
    base_die, pool_kwargs = _common_truncation(*dice)

    start = num_drop
    stop = num_keep + num_drop

    if base_die is not None:
        count_dice = slice(start, stop)
        return base_die.pool(count_dice=count_dice, **pool_kwargs).sum()

    # In the worst case, fall back to reduce().
    return _lowest_reduce(*dice, start=start, stop=stop)


def highest(*dice, num_keep=1, num_drop=0):
    """The highest outcome or sum of the highest outcomes among the dice.

    Args:
        *dice: The dice to be considered.
        num_keep: The number of highest dice will be summed.
        num_drop: This number of highest dice will be dropped before keeping dice
            to be summed.
    """
    if num_keep < 0:
        raise ValueError(f'num_drop={num_keep} cannot be negative.')
    if num_drop < 0:
        raise ValueError(f'num_drop={num_drop} cannot be negative.')

    if len(dice) == 0:
        return icepool.Die()
    dice = [icepool.Die(die) for die in dice]
    if num_keep == 0 or num_drop >= len(dice):
        return sum(die.zero() for die in dice)

    if num_keep == 1 and num_drop == 0:
        return _highest_single(*dice)
    elif num_keep >= len(dice) and num_drop == 0:
        return sum(dice)

    # Try to forumulate as a pool problem.
    base_die, pool_kwargs = _common_truncation(*dice)

    start = -(num_keep + (num_drop or 0))
    stop = -num_drop if num_drop > 0 else None

    if base_die is not None:
        count_dice = slice(start, stop)
        return base_die.pool(count_dice=count_dice, **pool_kwargs).sum()

    # In the worst case, fall back to reduce().
    return _highest_reduce(*dice, start=start, stop=stop)


def _lowest_single(*dice):
    """Roll all the dice and take the lowest single.

    The maximum outcome is equal to the least maximum outcome among all
    input dice.
    """
    dice = [icepool.Die(die) for die in dice]
    max_outcome = min(die.max_outcome() for die in dice)
    dice = [die.clip(max_outcome=max_outcome) for die in dice]
    dice = icepool.align(*dice)
    sweights = tuple(
        math.prod(t) for t in zip(*(die.sweights() for die in dice)))
    return icepool.from_sweights(dice[0].outcomes(), sweights)


def _highest_single(*dice):
    """Roll all the dice and take the highest single.

    The minimum outcome is equal to the greatest minimum outcome among all
    input dice.
    """
    dice = [icepool.Die(die) for die in dice]
    min_outcome = max(die.min_outcome() for die in dice)
    dice = [die.clip(min_outcome=min_outcome) for die in dice]
    dice = icepool.align(*dice)
    cweights = tuple(
        math.prod(t) for t in zip(*(die.cweights() for die in dice)))
    return icepool.from_cweights(dice[0].outcomes(), cweights)


def _lowest_reduce(*dice, start, stop):

    def inner_binary(so_far, x):
        return tuple(sorted(so_far + (x,))[:stop])

    rolls = icepool.reduce(inner_binary, dice, initial=())
    return rolls.sub(lambda t: sum(t[start:]))


def _highest_reduce(*dice, start, stop):

    def inner_binary(so_far, x):
        return tuple(sorted(so_far + (x,))[start:])

    rolls = icepool.reduce(inner_binary, dice, initial=())
    return rolls.sub(lambda t: sum(t[:stop]))


def _common_truncation(*dice):
    """Determines if the dice can be expressed as a one-sided truncation of a single base die.

    Returns:
        base_die, pool_kwargs
    """
    base_die = dice[0]
    truncate_max = True
    truncate_min = True
    for die in dice[1:]:
        if die.num_outcomes() == base_die.num_outcomes():
            if die.equals(base_die):
                continue
            else:
                return None, None

        if die.num_outcomes() > base_die.num_outcomes():
            base_die, die = die, base_die

        if truncate_min:
            for a, b in zip(reversed(die.items()), reversed(base_die.items())):
                if a != b:
                    truncate_min = False
                    break

        if truncate_max:
            for a, b in zip(die.items(), base_die.items()):
                if a != b:
                    truncate_max = False
                    break

        if not (truncate_min or truncate_max):
            return None, None

    if truncate_min and truncate_max:
        return base_die, {'num_dice': len(dice)}
    elif truncate_min:
        return base_die, {
            'truncate_min': tuple(die.min_outcome() for die in dice)
        }
    elif truncate_max:
        return base_die, {
            'truncate_max': tuple(die.max_outcome() for die in dice)
        }
    else:
        return None, None
