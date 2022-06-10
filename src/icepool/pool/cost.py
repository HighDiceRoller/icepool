__docformat__ = 'google'

import math


def can_truncate(dice) -> tuple[bool, bool]:
    """Determines if the dice can be expressed as a one-sided truncation of a single base die.

    Args:
        dice: A sequence of dice (already converted to dice).
    Returns:
        can_truncate_min, can_truncate_max: If both are true, all dice are
            identical.
    """
    if len(dice) == 0:
        return True, True
    base_die = dice[0]
    can_truncate_min = True
    can_truncate_max = True
    for die in dice[1:]:
        if die.num_outcomes() == base_die.num_outcomes():
            if die.equals(base_die):
                continue
            else:
                return False, False

        if die.num_outcomes() > base_die.num_outcomes():
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


def lo_hi_skip(count_dice: tuple[int, ...]) -> tuple[int, int]:
    """Returns the number of dice that can be skipped from the ends of count_dice.

    Returns:
        lo_skip: The number of dice that can be skipped on the low side.
        hi_skip: The number of dice that can be skipped on the high side.
    """
    for lo_skip, count in enumerate(count_dice):
        if count:
            break
    else:
        return len(count_dice), len(count_dice)

    for hi_skip, count in enumerate(reversed(count_dice)):
        if count:
            return lo_skip, hi_skip

    # Should never reach here.
    raise RuntimeError('Should not be reached.')


def estimate_costs(pool) -> tuple[int, int]:
    """Estimates the cost of popping from the min and max sides.

    Returns:
        pop_min_cost
        pop_max_cost
    """
    can_truncate_min, can_truncate_max = can_truncate(pool._dice.keys())
    if can_truncate_min or can_truncate_max:
        lo_skip, hi_skip = lo_hi_skip(pool.count_dice())
        die_sizes: list[int] = sum(
            ([die.num_outcomes()] * count for die, count in pool._dice.items()),
            start=[])
        die_sizes = sorted(die_sizes, reverse=True)
    if not can_truncate_min or not can_truncate_max:
        prod_cost = math.prod(
            die.num_outcomes()**count for die, count in pool._dice.items())

    if can_truncate_min:
        pop_min_cost = sum(die_sizes[hi_skip:])
    else:
        pop_min_cost = prod_cost

    if can_truncate_max:
        pop_max_cost = sum(die_sizes[lo_skip:])
    else:
        pop_max_cost = prod_cost

    return pop_min_cost, pop_max_cost
