__docformat__ = 'google'

import icepool


def is_die(arg) -> bool:
    return isinstance(arg, icepool.Die)


def is_deck(arg) -> bool:
    return isinstance(arg, icepool.Deck)


def is_dict(arg) -> bool:
    return hasattr(arg, 'keys') and hasattr(arg, 'values') and hasattr(
        arg, 'items') and hasattr(arg, '__getitem__')


def is_tuple(arg) -> bool:
    return type(arg) is tuple