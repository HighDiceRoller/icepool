__docformat__ = 'google'

import icepool

from collections import Counter, defaultdict
from functools import cache

from typing import Iterable, Mapping, MutableMapping
from icepool.typing import T


@cache
def _wallenius_weights(weight_die: icepool.Die[int], hand_size: int,
                       /) -> 'icepool.Die[tuple[int, ...]]':
    if hand_size == 0:
        return icepool.Die([()])

    def inner(weight):
        return (_wallenius_weights(weight_die.remove(weight, weight),
                                   hand_size - 1) +
                (weight, )).map(lambda x: tuple(sorted(x)))

    return weight_die.map(inner)


def wallenius(data: Iterable[tuple[T, int]]
              | Mapping[T, int | tuple[int, int]], hand_size: int,
              /) -> 'icepool.Die[T]':
    """EXPERIMENTAL: Wallenius' noncentral hypergeometric distribution.

    This is sampling without replacement with weights, where the entire weight
    of a card goes away when it is pulled.
    
    Args:
        data: Either an iterable of (outcome, weight), or a mapping from
            outcomes to either weights or (weight, quantity).
        hand_size: The number of outcomes to pull.
    
    Returns:
        A Die containing tuples of length `hand_size`.
    """
    # weight -> Deck
    weight_decks: 'MutableMapping[int, icepool.Deck[T]]' = {}
    if isinstance(data, Mapping):
        for outcome, v in data.items():
            if isinstance(v, int):
                quantity = 1
                weight = v
            else:
                weight, quantity = v
        weight_decks[weight] = weight_decks.get(weight, icepool.Deck()).append(
            outcome, quantity)
    else:
        for outcome, weight in data:
            weight_decks[weight] = weight_decks.get(
                weight, icepool.Deck()).append(outcome)

    weight_die: 'icepool.Die[int]' = icepool.Die({
        weight:
        weight * deck.denominator()
        for weight, deck in weight_decks.items()
    })

    hand_weights = _wallenius_weights(weight_die, hand_size)

    def inner(weights):
        weight_counts = Counter(weights)
        result = icepool.Die([()])
        for weight, count in weight_counts.items():
            result += weight_decks[weight].deal(count).expand()
            result = result.map(lambda x: tuple(sorted(x)))
        return result

    return hand_weights.map(inner, star=False)
