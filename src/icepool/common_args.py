__docformat__ = 'google'

import icepool

from typing import Any
from collections.abc import Mapping, Sequence


def itemize(keys: Mapping[Any, int] | Sequence,
            counts: Sequence | None) -> tuple[Sequence, Sequence[int]]:
    """Converts the argument(s) into a sequence of keys and a sequence of counts.

    Args:
        keys: One of the following:
            * A dict mapping keys to counts.
            * A sequence of keys, with one count per occurence.
        counts: Only compatible if keys is a sequence of the same length.
            Each element of keys counts times equal to the corresponding element
            of counts.
    """
    if is_dict(keys):
        if counts is not None:
            raise ValueError('counts cannot be used with a dict argument.')
        counts = tuple(keys.values())  # type: ignore
        keys = tuple(keys.keys())  # type: ignore
    else:
        keys = tuple(keys)
        if counts is None:
            counts = (1,) * len(keys)
        elif len(keys) != len(counts):
            raise ValueError('Length of keys must equal the number of counts.')
        else:
            counts = tuple(counts)

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