__docformat__ = 'google'

import icepool
from icepool.counts import CountsKeysView
from icepool.gen import GenGenerator, OutcomeCountGen
from icepool.math import iter_hypergeom

from functools import cached_property
import math


class Deal(OutcomeCountGen):
    """EXPERIMENTAL: Represents an unordered deal of cards from a deck.

    API and naming WIP.
    """

    _deck: 'icepool.Deck'
    _hand_sizes: tuple[int, ...]

    def __init__(self, deck: 'icepool.Deck', *hand_sizes: int):
        """Constructor.

        For algorithmic reasons, you must pre-commit to the number of cards to
        deal for each hand.

        Args:
            deck: The `Deck` to deal from.
            *hand_sizes: How many cards to deal. If multiple `hand_sizes` are
                provided, `OutcomeCountEval.next_state` will recieve one count
                per hand in order. Try to keep the number of hands to a minimum
                as this can be computationally intensive.
        """
        if any(hand < 0 for hand in hand_sizes):
            raise ValueError('hand_sizes cannot be negative.')
        self._deck = deck
        self._hand_sizes = hand_sizes
        if self.total_cards_dealt() > self.deck().num_cards():
            raise ValueError(
                'The total number of cards dealt cannot exceed the number of cards in the deck.'
            )

    def deck(self) -> 'icepool.Deck':
        """The deck the cards are dealt from."""
        return self._deck

    def hand_sizes(self) -> tuple[int, ...]:
        """The number of cards dealt to each hand as a tuple."""
        return self._hand_sizes

    def total_cards_dealt(self) -> int:
        """The total number of cards dealt."""
        return sum(self.hand_sizes())

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
        d_total = icepool.math.comb(self.deck().num_cards(),
                                    self.total_cards_dealt())
        d_split = math.prod(
            icepool.math.comb(self.total_cards_dealt(), h)
            for h in self.hand_sizes()[1:])
        return d_total * d_split

    def denominator(self) -> int:
        """The total number of possible deals."""
        return self._denomiator

    def _gen_common(self, popped_deck: 'icepool.Deck',
                    deck_count: int) -> GenGenerator:
        """Common implementation for _gen_min and _gen_max."""
        min_count = max(
            0, deck_count + self.total_cards_dealt() - self.deck().num_cards())
        max_count = min(deck_count, self.total_cards_dealt())
        for count_total in range(min_count, max_count + 1):
            weight_total = icepool.math.comb(deck_count, count_total)
            # The "deck" is the hand sizes.
            for counts, weight_split in iter_hypergeom(self.hand_sizes(),
                                                       count_total):
                popped_deal = Deal(
                    popped_deck,
                    *(h - c for h, c in zip(self.hand_sizes(), counts)))
                weight = weight_total * weight_split
                yield popped_deal, counts, weight

    def _gen_min(self, min_outcome) -> GenGenerator:
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, (0,), 1
            return

        popped_deck, deck_count = self.deck()._pop_min()

        yield from self._gen_common(popped_deck, deck_count)

    def _gen_max(self, max_outcome) -> GenGenerator:
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, (0,), 1
            return

        popped_deck, deck_count = self.deck()._pop_max()

        yield from self._gen_common(popped_deck, deck_count)

    def _estimate_direction_costs(self) -> tuple[int, int]:
        result = len(self.outcomes()) * math.prod(self.hand_sizes())
        return result, result

    @cached_property
    def _key_tuple(self) -> tuple:
        return Deal, self.deck(), self.hand_sizes()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Deal):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash
