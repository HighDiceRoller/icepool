__docformat__ = 'google'

import icepool
from icepool.collections import Counts
from icepool.typing import Outcome

import itertools
import math
from collections import defaultdict

from icepool.typing import T
from typing import Any, Iterable, Mapping, MutableMapping, Sequence


def itemize(keys: Mapping[Any, int] | Sequence,
            times: Sequence[int] | int) -> tuple[Sequence, Sequence[int]]:
    """Converts the arguments into a sequence of keys and a sequence of times.

    Args:
        keys: One of the following:
            * A dict mapping keys to times.
            * A sequence of keys, with one count per occurence.
        times: One of the following:
            * A sequence of `int`s of the same length as keys.
                Each count will be multiplied by the corresponding factor.
            * An `int`. All times will be multiplied by this factor.
    """
    try:
        len(keys)
    except TypeError:
        raise TypeError('Argument appears not to be a mapping or sequence.')

    if isinstance(times, int):
        times = (times,) * len(keys)
    else:
        if len(times) != len(keys):
            raise ValueError(
                f'The number of times ({len(times)}) must equal the number of keys ({len(keys)}).'
            )

    if isinstance(keys, Mapping):
        times = [v * x for v, x in zip(keys.values(), times)]
        keys = list(keys.keys())
    else:
        keys = list(keys)

    if any(x < 0 for x in times):
        raise ValueError('times cannot have negative values.')

    return keys, times


def expand_args_for_die(
        args: 'Sequence[T | icepool.Die[T] | icepool.RerollType]',
        times: Sequence[int]) -> Counts[T]:

    subdatas = [expand_arg(arg) for arg in args]
    data = merge_weights_lcm(subdatas, times)
    return Counts(data.items())


def expand_args_for_deck(
        args: 'Sequence[T | icepool.Deck[T] | icepool.RerollType]',
        times: Sequence[int]) -> Counts[T]:

    subdatas = [expand_arg(arg) for arg in args]
    data = merge_duplicates(subdatas, times)
    return Counts(data.items())


def expand_arg(
        arg: T | icepool.Population[T] | icepool.RerollType) -> Mapping[T, int]:
    if isinstance(arg, icepool.Population):
        return arg
    elif arg is icepool.Reroll:
        return {}
    elif isinstance(arg, tuple):
        if len(arg) == 0:
            return {(): 1}  # type: ignore
        sub_args: Iterable[Mapping[T, int]] = (
            expand_arg_inside_tuple(sub_arg) for sub_arg in arg)
        result: MutableMapping = defaultdict(int)
        for t in itertools.product(*(sub_arg.items() for sub_arg in sub_args)):
            outcomes, quantities = zip(*t)
            final_quantity = math.prod(quantities)
            result[outcomes] += final_quantity
        return result
    else:
        return {arg: 1}


def expand_arg_inside_tuple(
        arg: T | icepool.Population[T] | icepool.RerollType) -> Mapping[T, int]:
    if isinstance(arg, icepool.Again):
        raise TypeError('Again is not allowed inside tuple outcomes.')
    elif arg is icepool.Reroll:
        raise TypeError('Reroll is not allowed inside tuple outcomes.')
    else:
        return expand_arg(arg)


def merge_weights_lcm(subdatas: Sequence[Mapping[T, int]],
                      weights: Sequence[int]) -> Mapping[T, int]:
    """Merge for dice.

    Every subdata gets total weight proportional to the corresponding element of `weights`.

    The final denominator is equal to the primary denominator times the LCM of the secondary denominators.
    """
    if any(x < 0 for x in weights):
        raise ValueError('weights cannot be negative.')

    subdata_denominators = [sum(subdata.values()) for subdata in subdatas]

    denominator_lcm = math.lcm(*(d for d in subdata_denominators if d > 0))

    data: MutableMapping[Any, int] = defaultdict(int)
    for subdata, subdata_denominator, w in zip(subdatas, subdata_denominators,
                                               weights):
        factor = denominator_lcm * w // subdata_denominator if subdata_denominator else 0
        for outcome, weight in subdata.items():
            data[outcome] += weight * factor
    return data


def merge_duplicates(subdatas: Sequence[Mapping[T, int]],
                     duplicates: Sequence[int]) -> Mapping[T, int]:
    """Merge for decks.

    Every subdata gets dups equal to the corresponding element of duplicates
    times its original dups.
    """
    if any(x < 0 for x in duplicates):
        raise ValueError('duplicates cannot be negative.')

    data: MutableMapping[Any, int] = defaultdict(int)
    for subdata, subdup in zip(subdatas, duplicates):
        for outcome, dup in subdata.items():
            data[outcome] += dup * subdup

    return data
