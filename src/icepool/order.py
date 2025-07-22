__docformat__ = 'google'

import icepool

import enum

from typing import Collection


class OrderException(Exception):
    """An error related to outcome orderings."""


class OrderError(OrderException):
    """An unrecoverable error related to outcome orderings."""


class ConflictingOrderError(OrderError):
    """Indicates that two conflicting mandatory outcome orderings were encountered."""


class UnsupportedOrder(OrderException):
    """Indicates that the given order is not supported under the current context.
    
    It may still be possible that retrying with the opposite order will succeed.
    """


class Order(enum.IntEnum):
    """Can be used to define what order outcomes are seen in by MultisetEvaluators."""
    Ascending = 1
    Descending = -1
    Any = 0

    def merge(*orders: 'Order') -> 'Order':
        """Merges the given Orders.

        Returns:
            `Any` if all arguments are `Any`.
            `Ascending` if there is at least one `Ascending` in the arguments.
            `Descending` if there is at least one `Descending` in the arguments.

        Raises:
            `ConflictingOrderError` if both `Ascending` and `Descending` are in 
            the arguments.
        """
        result = Order.Any
        for order in orders:
            if (result > 0 and order < 0) or (result < 0 and order > 0):
                raise ConflictingOrderError(
                    f'Conflicting orders {orders}.\n' +
                    'Tip: If you are using highest(keep=k), try using lowest(drop=n-k) instead, or vice versa.'
                )
            if result == Order.Any:
                result = order
        return result

    def __neg__(self) -> 'Order':
        if self is Order.Ascending:
            return Order.Descending
        elif self is Order.Descending:
            return Order.Ascending
        else:
            return Order.Any


class OrderReason(enum.IntEnum):
    """Greater values represent higher priorities, which strictly override lower priorities."""
    Mandatory = 4
    """Something strictly requires this pop order."""
    PoolComposition = 3
    """The composition of dice in the pool favor this pop order."""
    KeepSkip = 2
    """The keep_tuple for allows more skips in this pop order."""
    Default = 1
    """This ordering is preferred by default."""
    NoPreference = 0
    """There is no preference for either pop order."""


def merge_order_preferences(
    *preferences: tuple[Order, OrderReason], ) -> tuple[Order, OrderReason]:
    """Returns a pop order that fits the highest priority preferences.
    
    Greater priorities strictly outrank lower priorities.
    Conflicting orders of the same priority are equal to an `Order.Any` of the
    next-higher priority, except for conflicitng `Mandatory` orders, which
    produces an exception.

    Raises:
        `ConflictingOrderError` if both `Ascending` and `Descending` are in 
        the arguments with `Mandatory` reason.
    """
    result_order = Order.Any
    result_reason = OrderReason.NoPreference
    for order, reason in preferences:
        if order == Order.Any or reason == OrderReason.NoPreference:
            continue
        elif reason > result_reason:
            result_order = order
            result_reason = reason
        elif reason == result_reason:
            if result_order == Order.Any:
                result_order = order
            elif result_order == order:
                continue
            elif result_reason < OrderReason.Mandatory:
                result_order = Order.Any
                result_reason = OrderReason(result_reason + 1)
            else:
                raise ConflictingOrderError(
                    f'Conflicting order preferences {preferences}.\n' +
                    'Tip: If you are using highest(keep=k), try using lowest(drop=n-k) instead, or vice versa.'
                )
    return result_order, result_reason


def pool_pop_order(pool: 'icepool.Pool') -> tuple[Order, OrderReason]:
    can_truncate_min, can_truncate_max = can_truncate(pool.unique_dice())
    if can_truncate_min and not can_truncate_max:
        return Order.Ascending, OrderReason.PoolComposition
    if can_truncate_max and not can_truncate_min:
        return Order.Descending, OrderReason.PoolComposition

    lo_skip, hi_skip = lo_hi_skip(pool.keep_tuple())
    if lo_skip > hi_skip:
        return Order.Ascending, OrderReason.KeepSkip
    if hi_skip > lo_skip:
        return Order.Descending, OrderReason.KeepSkip

    return Order.Any, OrderReason.NoPreference


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
