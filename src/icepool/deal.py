__docformat__ = 'google'

import icepool
from icepool.counts import CountsKeysView
from icepool.gen import OutcomeCountGen

from functools import cached_property

from typing import Generator


class Deal(OutcomeCountGen):
    """EXPERIMENTAL: Represents an unordered deal of cards from a deck.

    API and naming WIP.
    """

    _deck: 'icepool.Deck'
    _hand: int

    def __init__(self, deck, hand):
        self._deck = deck
        self._hand = hand
        if self.hand() > self.deck().num_cards():
            raise ValueError(
                'The total number of cards dealt cannot exceed the number of cards in the deck.'
            )

    def deck(self) -> 'icepool.Deck':
        """The deck the cards are dealt from."""
        return self._deck

    def hand(self) -> int:
        """The number of cards dealt."""
        return self._hand

    def outcomes(self) -> CountsKeysView:
        """The outcomes of the deck in sorted order.

        These are also the `keys` of the deck as a `Mapping`.
        Prefer to use the name `outcomes`.
        """
        return self.deck().outcomes()

    def _is_resolvable(self) -> bool:
        return len(self.outcomes()) > 0

    @cached_property
    def _denomiator(self) -> int:
        return icepool.math.comb(self.deck().num_cards(), self.hand())

    def denominator(self) -> int:
        """The total number of possible deals."""
        return self._denomiator

    def _gen_min(
            self, min_outcome
    ) -> Generator[tuple[OutcomeCountGen, int, int], None, None]:
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, 0, 1
            return

        popped_deck, deck_count = self.deck()._pop_min()

        min_count = max(0, deck_count + self.hand() - self.deck().num_cards())
        max_count = min(deck_count, self.hand())
        for count in range(min_count, max_count + 1):
            popped_deal = Deal(popped_deck, self.hand() - count)
            weight = icepool.math.comb(deck_count, count)
            yield popped_deal, count, weight

    def _gen_max(
            self, max_outcome
    ) -> Generator[tuple[OutcomeCountGen, int, int], None, None]:
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, 0, 1
            return

        popped_deck, deck_count = self.deck()._pop_max()

        min_count = max(0, deck_count + self.hand() - self.deck().num_cards())
        max_count = min(deck_count, self.hand())
        for count in range(min_count, max_count + 1):
            popped_deal = Deal(popped_deck, self.hand() - count)
            weight = icepool.math.comb(deck_count, count)
            yield popped_deal, count, weight

    def _estimate_direction_costs(self) -> tuple[int, int]:
        result = len(self.outcomes()) * self.hand()
        return result, result

    @cached_property
    def _key_tuple(self) -> tuple:
        return Deal, self.deck(), self.hand()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Deal):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash