__docformat__ = 'google'

import icepool
from icepool.collection.counts import Counts
from icepool.typing import U, Outcome

import itertools
import math
from collections import defaultdict

from icepool.typing import T
from typing import Any, Iterable, Mapping, MutableMapping, Sequence, Type, cast, overload

from icepool.collection.vector import Vector


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
        times = (times, ) * len(keys)
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
    return Counts(merge_weights_lcm(subdatas, times).items())


def expand_args_for_deck(
        args: 'Sequence[T | icepool.Deck[T] | icepool.RerollType]',
        times: Sequence[int]) -> Counts[T]:

    subdatas = [expand_arg(arg) for arg in args]
    return Counts(merge_duplicates(subdatas, times).items())


def expand_arg(
        arg: T | icepool.Population[T] | icepool.RerollType
) -> Mapping[T, int]:
    if isinstance(arg, icepool.Population):
        return arg
    elif arg is icepool.Reroll:
        return {}
    elif type(arg) == tuple:
        arg = cast('T | icepool.Population[T]',
                   icepool.cartesian_product(*arg, outcome_type=tuple))
        if type(arg) == tuple:
            return {arg: 1}  # type: ignore
        else:  # converted to Population
            return arg  # type: ignore
    else:
        return {arg: 1}


def merge_weights_lcm(subdatas: Sequence[Mapping[T, int]],
                      weights: Sequence[int]) -> Mapping[T, int]:
    """Merge for dice.

    Every subdata gets total weight proportional to the corresponding element of `weights`.
    """
    if any(x < 0 for x in weights):
        raise ValueError('weights cannot be negative.')

    subdata_denominators = [sum(subdata.values()) for subdata in subdatas]

    denominator_lcm = math.lcm(*(d // math.gcd(d, w)
                                 for d, w in zip(subdata_denominators, weights)
                                 if d > 0 and w > 0))

    data: MutableMapping[Any, int] = defaultdict(int)
    for subdata, subdata_denominator, w in zip(subdatas, subdata_denominators,
                                               weights):
        if subdata_denominator == 0 or w == 0:
            continue
        factor = denominator_lcm * w // subdata_denominator
        for outcome, weight in subdata.items():
            if weight == 0:
                continue
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
        if subdup == 0:
            continue
        for outcome, dup in subdata.items():
            if dup == 0:
                continue
            data[outcome] += dup * subdup

    return data
