__docformat__ = 'google'

import icepool
from icepool.collections import Counts

from collections import defaultdict
import itertools
import math


def expand_die_args(*args, weights, denominator_method):
    """Helper function to expand arguments to Die()."""
    if weights is not None:
        if len(weights) != len(args):
            raise ValueError(
                'If weights are provided, there must be exactly one weight per argument.'
            )
    else:
        weights = (1,) * len(args)

    # Special case: single die argument.
    if len(args) == 1 and _is_die(args[0]) and weights[0] == 1:
        return args[0]._data

    # Expand data.
    subdatas = [_expand(arg, denominator_method) for arg in args]
    data = _merge_subdatas(subdatas, weights, denominator_method)

    return Counts(sorted(data.items()))


def _expand(arg, denominator_method):
    """Expands the argument to a dict mapping outcomes to weights.

    The outcomes are valid outcomes for a die.
    """
    if _is_die(arg):
        return _expand_die(arg)
    elif _is_dict(arg):
        return _expand_dict(arg, denominator_method)
    elif _is_tuple(arg):
        return _expand_tuple(arg, denominator_method)
    else:
        return _expand_scalar(arg)


def _is_die(arg):
    return isinstance(arg, icepool.Die)


def _expand_die(arg):
    return arg._data


def _is_dict(arg):
    return hasattr(arg, 'keys') and hasattr(arg, 'values') and hasattr(
        arg, 'items') and hasattr(arg, '__getitem__')


def _expand_dict(arg, denominator_method):
    if len(arg) == 0:
        return {}
    subdatas = [_expand(k, denominator_method) for k, v in arg.items()]
    weights = [x for x in arg.values()]
    return _merge_subdatas(subdatas, weights, denominator_method)


def _is_tuple(arg):
    return type(arg) is tuple


def _expand_tuple(arg, denominator_method):
    if len(arg) == 0:
        return {(): 1}
    subdatas = [_expand(x, denominator_method) for x in arg]
    data = defaultdict(int)
    for t in itertools.product(*(subdata.items() for subdata in subdatas)):
        outcomes, weights = zip(*t)
        data[outcomes] += math.prod(weights)
    return data


def _expand_scalar(arg):
    if arg is icepool.Reroll:
        return {}
    else:
        return {arg: 1}


def _merge_subdatas(subdatas, weights, denominator_method):
    if any(x < 0 for x in weights):
        raise ValueError('Weights cannot be negative.')
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

    data = defaultdict(int)
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
