__docformat__ = 'google'

import icepool

from collections import Counter
from functools import cache

from typing import Generic, Iterable, Mapping, MutableMapping
from icepool.typing import T


@cache
def _wallenius_weights(weight_die: icepool.Die[int], hand_size: int,
                       /) -> 'icepool.Die[tuple[int, ...]]':
    """A die whose outcomes are sorted tuples of weights to pull."""
    if hand_size == 0:
        return icepool.Die([()])

    def inner(weight):
        return (_wallenius_weights(weight_die.remove(weight, weight),
                                   hand_size - 1) +
                (weight, )).map(lambda x: tuple(sorted(x)))

    return weight_die.map(inner)


class Wallenius(Generic[T]):
    """EXPERIMENTAL: Wallenius' noncentral hypergeometric distribution.

    This is sampling without replacement with weights, where the entire weight
    of a card goes away when it is pulled.
    """
    _weight_decks: 'MutableMapping[int, icepool.Deck[T]]'
    _weight_die: 'icepool.Die[int]'

    def __init__(self, data: Iterable[tuple[T, int]]
                 | Mapping[T, int | tuple[int, int]]):
        """Constructor.
        
        Args:
            data: Either an iterable of (outcome, weight), or a mapping from
                outcomes to either weights or (weight, quantity).
            hand_size: The number of outcomes to pull.
        """
        self._weight_decks = {}

        if isinstance(data, Mapping):
            for outcome, v in data.items():
                if isinstance(v, int):
                    weight = v
                    quantity = 1
                else:
                    weight, quantity = v
                self._weight_decks[weight] = self._weight_decks.get(
                    weight, icepool.Deck()).append(outcome, quantity)
        else:
            for outcome, weight in data:
                self._weight_decks[weight] = self._weight_decks.get(
                    weight, icepool.Deck()).append(outcome)

        self._weight_die = icepool.Die({
            weight: weight * deck.denominator()
            for weight, deck in self._weight_decks.items()
        })

    def deal(self, hand_size: int, /) -> 'icepool.MultisetExpression[T]':
        """Deals the specified number of outcomes from the Wallenius.
        
        The result is a `MultisetExpression` representing the multiset of
        outcomes dealt.
        """
        if hand_size == 0:
            return icepool.Pool([])

        def inner(weights):
            weight_counts = Counter(weights)
            result = None
            for weight, count in weight_counts.items():
                deal = self._weight_decks[weight].deal(count)
                if result is None:
                    result = deal
                else:
                    result = result + deal
            return result

        hand_weights = _wallenius_weights(self._weight_die, hand_size)
        return hand_weights.map_to_pool(inner, star=False)
