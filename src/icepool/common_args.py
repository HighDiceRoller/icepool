__docformat__ = 'google'

import icepool

from typing import Any
from collections.abc import Mapping, Sequence


def itemize(
        keys: Mapping[Any, int] | Sequence,
        counts: Sequence[int] | int | None) -> tuple[Sequence, Sequence[int]]:
    """Converts the argument(s) into a sequence of keys and a sequence of counts.

    Args:
        keys: One of the following:
            * A dict mapping keys to counts.
            * A sequence of keys, with one count per occurence.
        counts: One of the following:
            * A sequence of `int`s of the same length as keys.
                Each count will be multiplied by the corresponding factor.
            * An `int`. All counts will be multiplied by this factor.
    """
    if counts is None:
        counts = (1,) * len(keys)
    elif isinstance(counts, int):
        counts = (counts,) * len(keys)
    else:
        if len(counts) != len(keys):
            raise ValueError(
                'The number of counts must equal the number of keys.')

    if is_dict(keys):
        counts = tuple(
            v * x for v, x in zip(keys.values(), counts))  # type: ignore
        keys = tuple(keys.keys())  # type: ignore
    else:
        keys = tuple(keys)

    if any(x < 0 for x in counts):
        raise ValueError('counts cannot have negative values.')

    return keys, counts


def is_die(arg) -> bool:
    return isinstance(arg, icepool.Die)


def is_deck(arg) -> bool:
    return isinstance(arg, icepool.Deck)


def is_dict(arg) -> bool:
    return hasattr(arg, 'keys') and hasattr(arg, 'values') and hasattr(
        arg, 'items') and hasattr(arg, '__getitem__')


def is_tuple(arg) -> bool:
    return type(arg) is tuple