__docformat__ = 'google'

import icepool

import math

from typing import Collection


def can_truncate(dice: Collection['icepool.Die']) -> tuple[bool, bool]:
    """Determines if the dice can be expressed as a one-sided truncation of a single base `Die`.

    Args:
        dice: A sequence of dice.
    Returns:
        can_truncate_min, can_truncate_max: If both are true, all dice are
            identical.
    """
    if len(dice) == 0:
        return True, True
    dice_iter = iter(dice)
    base_die = next(dice_iter)
    can_truncate_min = True
    can_truncate_max = True
    for die in dice_iter:
        if len(die) == len(base_die):
            if die.equals(base_die):
                continue
            else:
                return False, False

        if len(die) > len(base_die):
            base_die, die = die, base_die

        if can_truncate_min:
            for a, b in zip(reversed(die.items()), reversed(base_die.items())):
                if a != b:
                    can_truncate_min = False
                    break

        if can_truncate_max:
            for a, b in zip(die.items(), base_die.items()):
                if a != b:
                    can_truncate_max = False
                    break

        if not (can_truncate_min or can_truncate_max):
            return False, False

    return can_truncate_min, can_truncate_max


def lo_hi_skip(keep_tuple: tuple[int, ...]) -> tuple[int, int]:
    """The number of dice that can be skipped from the ends of keep_tuple.

    Returns:
        lo_skip: The number of dice that can be skipped on the low side.
        hi_skip: The number of dice that can be skipped on the high side.
    """
    for lo_skip, count in enumerate(keep_tuple):
        if count:
            break
    else:
        return len(keep_tuple), len(keep_tuple)

    for hi_skip, count in enumerate(reversed(keep_tuple)):
        if count:
            return lo_skip, hi_skip

    # Should never reach here.
    raise RuntimeError('Should not be reached.')


def estimate_costs(pool: 'icepool.Pool') -> tuple[int, int]:
    """Estimates the cost of popping from the min and max sides.

    Returns:
        pop_min_cost: A positive `int`.
        pop_max_cost: A positive `int`.
    """
    can_truncate_min, can_truncate_max = can_truncate(pool.unique_dice())
    if can_truncate_min or can_truncate_max:
        lo_skip, hi_skip = lo_hi_skip(pool.keep_tuple())
        die_sizes: list[int] = sum(
            ([len(die)] * count for die, count in pool._dice), start=[])
        die_sizes = sorted(die_sizes, reverse=True)
    if not can_truncate_min or not can_truncate_max:
        prod_cost = math.prod(len(die)**count for die, count in pool._dice)

    if can_truncate_min:
        pop_min_cost = sum(die_sizes[hi_skip:])
    else:
        pop_min_cost = prod_cost

    if can_truncate_max:
        pop_max_cost = sum(die_sizes[lo_skip:])
    else:
        pop_max_cost = prod_cost

    return pop_min_cost, pop_max_cost
