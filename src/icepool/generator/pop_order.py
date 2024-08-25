__docformat__ = 'google'

import icepool

import enum
import math

from typing import Collection, Iterable

from icepool.typing import Order


class PopOrderReason(enum.IntEnum):
    """Greater values represent higher priorities, which strictly override lower priorities."""
    PoolComposition = 2
    """The composition of dice in the pool favor this pop order."""
    KeepSkip = 1
    """The keep_tuple for allows more skips in this pop order."""
    NoPreference = 0
    """There is no preference for either pop order."""


def merge_pop_orders(
    *preferences: tuple[Order | None, PopOrderReason],
) -> tuple[Order | None, PopOrderReason]:
    """Returns a pop order that fits the highest priority preferences.
    
    Greater priorities strictly outrank lower priorities.
    An order of `None` represents conflicting orders and can occur in the 
    argument and/or return value.
    """
    result_order: Order | None = Order.Any
    result_reason = PopOrderReason.NoPreference
    for order, reason in preferences:
        if order == Order.Any or reason == PopOrderReason.NoPreference:
            continue
        elif reason > result_reason:
            result_order = order
            result_reason = reason
        elif reason == result_reason:
            if result_order == Order.Any:
                result_order = order
            elif result_order == order:
                continue
            else:
                result_order = None
    return result_order, result_reason


def pool_pop_order(pool: 'icepool.Pool') -> tuple[Order, PopOrderReason]:
    can_truncate_min, can_truncate_max = can_truncate(pool.unique_dice())
    if can_truncate_min and not can_truncate_max:
        return Order.Ascending, PopOrderReason.PoolComposition
    if can_truncate_max and not can_truncate_min:
        return Order.Descending, PopOrderReason.PoolComposition

    lo_skip, hi_skip = lo_hi_skip(pool.keep_tuple())
    if lo_skip > hi_skip:
        return Order.Ascending, PopOrderReason.KeepSkip
    if hi_skip > lo_skip:
        return Order.Descending, PopOrderReason.KeepSkip

    return Order.Any, PopOrderReason.NoPreference


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
