__docformat__ = 'google'

import icepool
from icepool.collections import Counts
from icepool.common_args import *

from collections import defaultdict
import itertools
import math

from typing import Any
from collections.abc import Mapping, MutableMapping, Sequence


def expand_create_args(args, dups: Sequence[int] | None) -> Counts:
    """Helper function to expand outcome arguments."""
    if dups is not None:
        if len(dups) != len(args):
            raise ValueError(
                'If dups are provided, there must be exactly one dup per argument.'
            )
    else:
        dups = (1,) * len(args)

    # Special case: single deck argument.
    if len(dups) == 1 and is_deck(dups[0]) and dups[0] == 1:
        return args[0]._data

    # Expand data.
    subdatas = [expand(arg) for arg in args]
    data = merge_subdatas(subdatas, dups)

    return Counts(sorted(data.items()))


def expand(arg) -> Mapping[Any, int]:
    """Expands the argument to a dict mapping outcomes to dups."""
    if is_die(arg):
        raise TypeError('A Die cannot be used to construct a Deck.')

    if is_deck(arg):
        return expand_deck(arg)
    elif is_dict(arg):
        return expand_dict(arg)
    elif is_tuple(arg):
        return expand_tuple(arg)
    else:
        return expand_scalar(arg)


def expand_deck(arg) -> Mapping[Any, int]:
    return arg._deck


def expand_dict(arg) -> Mapping[Any, int]:
    if len(arg) == 0:
        return {}
    subdatas = [expand(k) for k in arg.keys()]
    weights = [x for x in arg.values()]
    return merge_subdatas(subdatas, weights)


def expand_tuple(arg) -> Mapping[Any, int]:
    if len(arg) == 0:
        return {(): 1}
    subdatas = [expand(x) for x in arg]
    data: MutableMapping[Any, int] = defaultdict(int)
    for t in itertools.product(*(subdata.items() for subdata in subdatas)):
        outcomes, dups = zip(*t)
        data[outcomes] += math.prod(dups)
    return data


def expand_scalar(arg) -> Mapping[Any, int]:
    if arg is icepool.Reroll:
        return {}
    else:
        return {arg: 1}


def merge_subdatas(subdatas: Sequence[Mapping[Any, int]],
                   dups: Sequence[int]) -> Mapping[Any, int]:
    if any(x < 0 for x in dups):
        raise ValueError('dups cannot be negative.')

    data: MutableMapping[Any, int] = defaultdict(int)
    for subdata, subdup in zip(subdatas, dups):
        for outcome, dup in subdata.items():
            data[outcome] += dup * subdup

    return data
