__docformat__ = 'google'

import icepool

import math

from icepool.typing import Outcome, T
from typing import Iterable, Literal, Sequence, cast, overload


def lowest_slice(keep: int | None = None, drop: int | None = None) -> slice:
    """Converts keep and drop lowest into a slice."""
    if keep is not None and keep < 0:
        raise ValueError(f'keep={keep} cannot be negative.')
    if drop is not None and drop < 0:
        raise ValueError(f'drop={drop} cannot be negative.')
    if drop is None:
        if keep is None:
            keep = 1
        start = 0
        stop = keep
    else:
        start = drop
        if keep is None:
            stop = None
        else:
            stop = drop + keep
    return slice(start, stop)


def highest_slice(keep: int | None = None, drop: int | None = None) -> slice:
    """Converts keep and drop highest into a slice."""
    if keep is not None and keep < 0:
        raise ValueError(f'keep={keep} cannot be negative.')
    if drop is not None and drop < 0:
        raise ValueError(f'drop={drop} cannot be negative.')
    if drop is None:
        if keep is None:
            keep = 1
        if keep > 0:
            start = -keep
            stop = None
        else:
            start = 0
            stop = 0
    else:
        if drop == 0:
            stop = None
        else:
            stop = -drop

        if keep is None:
            start = None
        elif keep > 0:
            start = -(keep + drop)
        else:
            start = 0
            stop = 0
    return slice(start, stop)


def canonical_slice(original: slice, length: int) -> slice:
    """Produces a slice that has 0 <= start <= stop <= length.
    
    Assumes the original step is positive.
    """

    if original.start is None:
        start = 0
    elif original.start < 0:
        start = max(0, length + original.start)
    else:
        start = min(original.start, length)

    if original.stop is None:
        stop = length
    elif original.stop < 0:
        stop = max(0, length + original.stop)
    else:
        stop = min(original.stop, length)

    if start > stop:
        stop = start
    return slice(start, stop, original.step)


@overload
def lowest(iterable: 'Iterable[T | icepool.Die[T]]', /) -> 'icepool.Die[T]':
    ...


@overload
def lowest(arg0: 'T | icepool.Die[T]', arg1: 'T | icepool.Die[T]', /, *args:
           'T | icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def lowest(arg0,
           /,
           *more_args: 'T | icepool.Die[T]',
           keep: int | None = None,
           drop: int | None = None,
           default: T | None = None) -> 'icepool.Die[T]':
    """The lowest outcome among the rolls, or the sum of some of the lowest.

    The outcomes should support addition and multiplication if `keep != 1`.

    Args:
        args: Dice or individual outcomes in a single iterable, or as two or
            more separate arguments. Similar to the built-in `min()`.
        keep, drop: These arguments work together:
            * If neither are provided, the single lowest die will be taken.
            * If only `keep` is provided, the `keep` lowest dice will be summed.
            * If only `drop` is provided, the `drop` lowest dice will be dropped
                and the rest will be summed.
            * If both are provided, `drop` lowest dice will be dropped, then
                the next `keep` lowest dice will be summed.
        default: If an empty iterable is provided, the result will be a die that
            always rolls this value.

    Raises:
        ValueError if an empty iterable is provided with no `default`.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0, ) + more_args

    if len(args) == 0:
        if default is None:
            raise ValueError(
                "lowest() arg is an empty sequence and no default was provided."
            )
        else:
            return icepool.Die([default])

    index_slice = lowest_slice(keep, drop)
    return _sum_slice(*args, index_slice=index_slice)


@overload
def highest(iterable: 'Iterable[T | icepool.Die[T]]', /) -> 'icepool.Die[T]':
    ...


@overload
def highest(arg0: 'T | icepool.Die[T]', arg1: 'T | icepool.Die[T]', /, *args:
            'T | icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def highest(arg0,
            /,
            *more_args: 'T | icepool.Die[T]',
            keep: int | None = None,
            drop: int | None = None,
            default: T | None = None) -> 'icepool.Die[T]':
    """The highest outcome among the rolls, or the sum of some of the highest.

    The outcomes should support addition and multiplication if `keep != 1`.

    Args:
        args: Dice or individual outcomes in a single iterable, or as two or
            more separate arguments. Similar to the built-in `max()`.
        keep, drop: These arguments work together:
            * If neither are provided, the single highest die will be taken.
            * If only `keep` is provided, the `keep` highest dice will be summed.
            * If only `drop` is provided, the `drop` highest dice will be dropped
                and the rest will be summed.
            * If both are provided, `drop` highest dice will be dropped, then
                the next `keep` highest dice will be summed.
        drop: This number of highest dice will be dropped before keeping dice
            to be summed.
        default: If an empty iterable is provided, the result will be a die that
            always rolls this value.

    Raises:
        ValueError if an empty iterable is provided with no `default`.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0, ) + more_args

    if len(args) == 0:
        if default is None:
            raise ValueError(
                "highest() arg is an empty sequence and no default was provided."
            )
        else:
            return icepool.Die([default])

    index_slice = highest_slice(keep, drop)
    return _sum_slice(*args, index_slice=index_slice)


@overload
def middle(iterable: 'Iterable[T | icepool.Die[T]]', /) -> 'icepool.Die[T]':
    ...


@overload
def middle(arg0: 'T | icepool.Die[T]', arg1: 'T | icepool.Die[T]', /, *args:
           'T | icepool.Die[T]') -> 'icepool.Die[T]':
    ...


def middle(arg0,
           /,
           *more_args: 'T | icepool.Die[T]',
           keep: int = 1,
           tie: Literal['error', 'high', 'low'] = 'error',
           default: T | None = None) -> 'icepool.Die[T]':
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
        default: If an empty iterable is provided, the result will be a die that
            always rolls this value.

    Raises:
        ValueError if an empty iterable is provided with no `default`.
    """
    if len(more_args) == 0:
        args = arg0
    else:
        args = (arg0, ) + more_args

    if len(args) == 0:
        if default is None:
            raise ValueError(
                "middle() arg is an empty sequence and no default was provided."
            )
        else:
            return icepool.Die([default])

    # Expression evaluators are difficult to type.
    return icepool.Pool(args).middle(keep, tie=tie).sum()  # type: ignore


def _sum_slice(*args, index_slice: slice) -> 'icepool.Die':
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

    # Faster special cases.
    canonical = canonical_slice(index_slice, len(dice))

    # Zero-size slice.
    # The inputs should support addition.
    if canonical.start == canonical.stop:
        return sum(die.zero() for die in dice)  # type: ignore

    # All dice selected.
    if canonical.start == 0 and canonical.stop == len(dice):
        return sum(dice)  # type: ignore

    if canonical.start == 0 and canonical.stop == 1:
        return _lowest_single(*dice)

    if canonical.start == len(dice) - 1 and canonical.stop == len(dice):
        return _highest_single(*dice)

    # Use pool.
    # Expression evaluators are difficult to type.
    return icepool.Pool(dice)[index_slice].sum()  # type: ignore


def _lowest_single(*args: 'T | icepool.Die[T]') -> 'icepool.Die[T]':
    """Roll all the dice and take the lowest single one.

    The maximum outcome is equal to the least maximum outcome among all
    input dice.
    """
    dice = tuple(icepool.implicit_convert_to_die(arg) for arg in args)
    max_outcome = min(die.max_outcome() for die in dice)
    dice = tuple(die.clip(max_outcome=max_outcome) for die in dice)
    outcomes = icepool.sorted_union(*dice)
    quantities_ge = tuple(
        math.prod(die.quantity('>=', outcome) for die in dice)
        for outcome in outcomes)
    return icepool.from_cumulative(outcomes,
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
    outcomes = icepool.sorted_union(*dice)
    quantities_le = tuple(
        math.prod(die.quantity('<=', outcome) for die in dice)
        for outcome in outcomes)
    return icepool.from_cumulative(outcomes, quantities_le)
