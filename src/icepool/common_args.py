__docformat__ = 'google'

import icepool

from typing import Any
from collections.abc import Mapping, Sequence


def itemize(
        keys: Mapping[Any, int] | Sequence,
        times: Sequence[int] | int | None) -> tuple[Sequence, Sequence[int]]:
    """Converts the argument(s) into a sequence of keys and a sequence of counts.

    Args:
        keys: One of the following:
            * A dict mapping keys to times.
            * A sequence of keys, with one count per occurence.
        times: One of the following:
            * A sequence of `int`s of the same length as keys.
                Each count will be multiplied by the corresponding factor.
            * An `int`. All times will be multiplied by this factor.
    """
    if times is None:
        times = (1,) * len(keys)
    elif isinstance(times, int):
        times = (times,) * len(keys)
    else:
        if len(times) != len(keys):
            raise ValueError(
                'The number of times must equal the number of keys.')

    if is_dict(keys):
        times = tuple(
            v * x for v, x in zip(keys.values(), times))  # type: ignore
        keys = tuple(keys.keys())  # type: ignore
    else:
        keys = tuple(keys)

    if any(x < 0 for x in times):
        raise ValueError('counts cannot have negative values.')

    return keys, times


def is_die(arg) -> bool:
    return isinstance(arg, icepool.Die)


def is_deck(arg) -> bool:
    return isinstance(arg, icepool.Deck)


def is_dict(arg) -> bool:
    return hasattr(arg, 'keys') and hasattr(arg, 'values') and hasattr(
        arg, 'items') and hasattr(arg, '__getitem__')


def is_tuple(arg) -> bool:
    return type(arg) is tuple