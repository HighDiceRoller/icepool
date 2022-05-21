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

    start = min(num_drop, len(dice))
    stop = min(num_keep + num_drop, len(dice))
    return _keep(*dice, start=start, stop=stop)


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

    start = len(dice) - min(num_keep + num_drop, len(dice))
    stop = len(dice) - min(num_drop, len(dice))
    return _keep(*dice, start=start, stop=stop)


def _keep(*dice, start, stop):
    """Common code for `lowest` and `highest`.

    Args:
        *dice: The dice (not converted to `Die` yet).
        start, stop: The slice `start:stop` will be kept. These will be between
            0 and len(dice) inclusive.
    """
    dice = [icepool.Die(die) for die in dice]

    if len(dice) == 0 or any(die.is_empty() for die in dice):
        return icepool.Die()

    if start == stop:
        return sum(die.zero() for die in dice)

    if start == 0 and stop == len(dice):
        return sum(dice)

    if stop == 1:
        return _lowest_single(*dice)

    if start == len(dice) - 1:
        return _highest_single(*dice)

    # Try to forumulate as a pool problem.
    base_die, pool_kwargs = _common_truncation(*dice)
    if base_die is not None:
        return base_die.pool(count_dice=slice(start, stop), **pool_kwargs).sum()

    # In the worst case, fall back to reduce()-based algorithm.
    return _keep_reduce(*dice, start=start, stop=stop)


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


def _keep_reduce(*dice, start, stop):
    """Fallback algorithm for keep.

    Tracks the k lowest or highest dice, whichever is more efficient.

    Args:
        *dice
        start, stop: The slice `start:stop` will be kept. These will be between
            0 and len(dice) inclusive. At least one die will be kept at this
            point.
    """
    if start <= len(dice) - stop:
        return _lowest_reduce(*dice, start=start, stop=stop)
    else:
        return _highest_reduce(*dice, start=start, stop=stop)


def _lowest_reduce(*dice, start, stop):

    # Sort the dice by a heuristic to try to reduce the average state size.
    def sort_key(die):
        return die.num_outcomes()

    dice = sorted(dice, key=sort_key)

    def inner_binary(so_far, x):
        return tuple(sorted(so_far + (x,))[:stop])

    rolls = icepool.reduce(inner_binary, dice, initial=())
    return rolls.sub(lambda t: sum(t[start:]))


def _highest_reduce(*dice, start, stop):

    # Sort the dice by a heuristic to try to reduce the average state size.
    def sort_key(die):
        return die.num_outcomes()

    dice = sorted(dice, key=sort_key)

    # Make indexes negative.
    start = start - len(dice)
    # 0 must be replaced by None or else the slice will be empty.
    stop = (stop - len(dice)) or None

    def inner_binary(so_far, x):
        return tuple(sorted(so_far + (x,))[start:])

    rolls = icepool.reduce(inner_binary, dice, initial=())
    return rolls.sub(lambda t: sum(t[:stop]))


def _common_truncation(*dice):
    """Determines if the dice can be expressed as a one-sided truncation of a single base die.

    Args:
        dice: A sequence of dice (already converted to dice).

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
