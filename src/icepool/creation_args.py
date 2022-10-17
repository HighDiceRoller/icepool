__docformat__ = 'google'

import icepool
from icepool.counts import Counts

import itertools
import math
from collections import defaultdict

from typing import Any, Callable, Mapping, MutableMapping, Sequence, TypeAlias


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
        times = [v * x for v, x in zip(keys.values(), times)]  # type: ignore
        keys = list(keys.keys())  # type: ignore
    else:
        keys = list(keys)

    if any(x < 0 for x in times):
        raise ValueError('times cannot have negative values.')

    return keys, times


def expand_args_for_die(args: Sequence, times: Sequence[int]) -> Counts:
    subdatas = [expand(arg, merge_weights_lcm) for arg in args]
    data = merge_weights_lcm(subdatas, times)
    return Counts(data.items())


def expand_args_for_deck(args: Sequence, times: Sequence[int]) -> Counts:
    subdatas = [expand(arg, merge_duplicates) for arg in args]
    data = merge_duplicates(subdatas, times)
    return Counts(data.items())


MergeFunc: TypeAlias = Callable[[Sequence[Mapping[Any, int]], Sequence[int]],
                                Mapping[Any, int]]


def expand(arg, merge_func: MergeFunc):

    if isinstance(arg, Mapping):
        return expand_dict(arg, merge_func)
    elif isinstance(arg, tuple):
        return expand_tuple(arg, merge_func)
    elif isinstance(arg, (str, bytes)):
        return expand_scalar(arg)
    elif isinstance(arg, Sequence):
        return expand_sequence(arg, merge_func)
    else:
        return expand_scalar(arg)


def expand_dict(arg, merge_func: MergeFunc) -> Mapping[Any, int]:
    subdatas = [expand(k, merge_func) for k in arg.keys()]
    weights = [v for v in arg.values()]
    return merge_func(subdatas, weights)


def expand_tuple(arg, merge_func: MergeFunc) -> Mapping[Any, int]:
    if len(arg) == 0:
        return {(): 1}
    subdatas = [expand(x, merge_func) for x in arg]
    data: MutableMapping[Any, int] = defaultdict(int)
    for t in itertools.product(*(subdata.items() for subdata in subdatas)):
        outcomes, duplicates = zip(*t)
        data[outcomes] += math.prod(duplicates)
    return data


def expand_sequence(arg, merge_func: MergeFunc) -> Mapping[Any, int]:
    subdatas = [expand(x, merge_func) for x in arg]
    weights = [1] * len(subdatas)
    return merge_func(subdatas, weights)


def expand_scalar(arg) -> Mapping[Any, int]:
    if arg is icepool.Reroll:
        return {}
    else:
        return {arg: 1}


def merge_weights_lcm(subdatas: Sequence[Mapping[Any, int]],
                      weights: Sequence[int]) -> Mapping[Any, int]:
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


def merge_duplicates(subdatas: Sequence[Mapping[Any, int]],
                     duplicates: Sequence[int]) -> Mapping[Any, int]:
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
