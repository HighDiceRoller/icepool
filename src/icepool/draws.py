__docformat__ = 'google'

import icepool
from icepool.counts import Counts, CountsKeysView
from icepool.gen import OutcomeCountGen

from functools import cached_property

from typing import Generator


class Draws(OutcomeCountGen):
    """EXPERIMENTAL: Represents a draw of cards from a deck.

    API and naming WIP.
    """

    _deck: 'icepool.Deck'
    _draws: int

    def __init__(self, deck, draws):
        self._deck = deck
        self._draws = draws
        if self.draws() > self.deck().size():
            raise ValueError('draws cannot exceed deck_size.')

    def deck(self) -> 'icepool.Deck':
        return self._deck

    def draws(self) -> int:
        return self._draws

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
        return icepool.math.comb(self.deck().size(), self.draws())

    def denominator(self) -> int:
        return self._denomiator

    def _gen_min(
            self, min_outcome
    ) -> Generator[tuple[OutcomeCountGen, int, int], None, None]:
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, 0, 1
            return

        popped_deck, deck_count = self.deck()._pop_min()

        min_count = max(0, deck_count + self.draws() - self.deck().size())
        max_count = min(deck_count, self.draws())
        for count in range(min_count, max_count + 1):
            popped_draws = Draws(popped_deck, self.draws() - count)
            weight = icepool.math.comb(deck_count, count)
            yield popped_draws, count, weight

    def _gen_max(
            self, max_outcome
    ) -> Generator[tuple[OutcomeCountGen, int, int], None, None]:
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, 0, 1
            return

        popped_deck, deck_count = self.deck()._pop_max()

        min_count = max(0, deck_count + self.draws() - self.deck().size())
        max_count = min(deck_count, self.draws())
        for count in range(min_count, max_count + 1):
            popped_draws = Draws(popped_deck, self.draws() - count)
            weight = icepool.math.comb(deck_count, count)
            yield popped_draws, count, weight

    def _estimate_direction_costs(self) -> tuple[int, int]:
        result = len(self.outcomes()) * self.draws()
        return result, result

    @cached_property
    def _key_tuple(self) -> tuple:
        return Draws, self.deck(), self.draws()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Draws):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash