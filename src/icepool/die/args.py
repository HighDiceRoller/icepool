__docformat__ = 'google'

import icepool
from icepool.collections import Counts

from collections import defaultdict
import itertools
import math

from typing import Any
from collections.abc import Mapping, MutableMapping, Sequence


def expand_create_args(*args, weights: Sequence[int] | None,
                       denominator_method: str) -> Counts:
    """Helper function to expand outcome arguments."""
    if weights is not None:
        if len(weights) != len(args):
            raise ValueError(
                'If weights are provided, there must be exactly one weight per argument.'
            )
    else:
        weights = (1,) * len(args)

    # Special case: single die argument.
    if len(args) == 1 and is_die(args[0]) and weights[0] == 1:
        return args[0]._data

    # Expand data.
    subdatas = [expand(arg, denominator_method) for arg in args]
    data = merge_subdatas(subdatas, weights, denominator_method)

    return Counts(sorted(data.items()))


def expand(arg, denominator_method: str) -> Mapping[Any, int]:
    """Expands the argument to a dict mapping outcomes to weights."""
    if is_deck(arg):
        raise TypeError('A Deck cannot be used to construct a Die.')

    if is_die(arg):
        return expand_die(arg)
    elif is_dict(arg):
        return expand_dict(arg, denominator_method)
    elif is_tuple(arg):
        return expand_tuple(arg, denominator_method)
    else:
        return expand_scalar(arg)


def is_die(arg) -> bool:
    return isinstance(arg, icepool.Die)


def is_deck(arg) -> bool:
    return isinstance(arg, icepool.CardDraw)


def is_dict(arg) -> bool:
    return hasattr(arg, 'keys') and hasattr(arg, 'values') and hasattr(
        arg, 'items') and hasattr(arg, '__getitem__')


def is_tuple(arg) -> bool:
    return type(arg) is tuple


def expand_die(arg) -> Mapping[Any, int]:
    return arg._data


def expand_dict(arg, denominator_method: str) -> Mapping[Any, int]:
    if len(arg) == 0:
        return {}
    subdatas = [expand(k, denominator_method) for k, v in arg.items()]
    weights = [x for x in arg.values()]
    return merge_subdatas(subdatas, weights, denominator_method)


def expand_tuple(arg, denominator_method: str) -> Mapping[Any, int]:
    if len(arg) == 0:
        return {(): 1}
    subdatas = [expand(x, denominator_method) for x in arg]
    data: MutableMapping[Any, int] = defaultdict(int)
    for t in itertools.product(*(subdata.items() for subdata in subdatas)):
        outcomes, weights = zip(*t)
        data[outcomes] += math.prod(weights)
    return data


def expand_scalar(arg) -> Mapping[Any, int]:
    if arg is icepool.Reroll:
        return {}
    else:
        return {arg: 1}


def merge_subdatas(subdatas: Sequence[Mapping[Any,
                                              int]], weights: Sequence[int],
                   denominator_method: str) -> Mapping[Any, int]:
    if any(x < 0 for x in weights):
        raise ValueError('weights cannot be negative.')
    subdata_denominators = [sum(subdata.values()) for subdata in subdatas]

    if denominator_method == 'prod':
        denominator_prod = math.prod(d for d in subdata_denominators if d > 0)
    elif denominator_method == 'lcm':
        denominator_prod = math.lcm(*(d for d in subdata_denominators if d > 0))
    elif denominator_method in ['lcm_weighted', 'reduce']:
        denominator_prod = math.lcm(
            *(d // math.gcd(d, w)
              for d, w in zip(subdata_denominators, weights)
              if d > 0))
    else:
        raise ValueError(f'Invalid denominator_method {denominator_method}.')

    data: MutableMapping[Any, int] = defaultdict(int)
    for subdata, subdata_denominator, w in zip(subdatas, subdata_denominators,
                                               weights):
        factor = denominator_prod * w // subdata_denominator if subdata_denominator else 0
        for outcome, weight in subdata.items():
            data[outcome] += weight * factor

    if denominator_method == 'reduce':
        gcd = math.gcd(*data.values())
        if gcd > 1:
            data = {outcome: weight // gcd for outcome, weight in data.items()}

    return data
