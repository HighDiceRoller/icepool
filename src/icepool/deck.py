__docformat__ = 'google'

import icepool
import icepool.math
import icepool.creation_args
from icepool.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.generator import OutcomeCountGen

from functools import cached_property

from typing import Any, Generator, Iterator
from collections.abc import Mapping, Sequence


class Deck(OutcomeCountGen, Mapping[Any, int]):
    """EXPERIMENTAL: Represents drawing a hand from a deck.

    In other words, this is sampling without replacement.
    """

    _data: Counts
    _hand_size: int

    def __new__(cls,
                cards: Mapping[Any, int] | Sequence,
                times: Sequence[int] | int = 1,
                *,
                hand_size: int):
        """Constructor for a deck.

        Args:
            cards: The cards of the deck. This can be one of the following:
                * A Mapping from cards to dups.
                * A sequence of cards.

                Note that `Die` and `Deck` both count as Mappings.

                Each card may be one of the following:
                * A Mapping from cards to dups.
                * A tuple of cards.
                    Any tuple elements that are Mappings will expand the
                    tuple according to their Cartesian product.
                    Use this carefully since it may create a large number of
                    cards.
                * Anything else will be treated as a scalar.
            times: Multiplies the number of times each element of `cards`
                will be put into the deck.
                `times` can either be a sequence of the same length as
                `cards` or a single `int` to apply to all elements of
                `cards`.
        """
        if isinstance(cards, Deck):
            if times == 1:
                return cards
            else:
                cards = cards._data

        cards, times = icepool.creation_args.itemize(cards, times)

        if len(cards) == 1 and times[0] == 1 and isinstance(cards[0], Deck):
            return cards[0]

        self = super(Deck, cls).__new__(cls)
        self._data = icepool.creation_args.expand_args_for_deck(cards, times)
        self._hand_size = hand_size
        if self.hand_size() > self.deck_size():
            raise ValueError('hand_size cannot exceed deck_size.')
        return self

    def cards(self) -> CountsKeysView:
        return self._data.keys()

    outcomes = cards

    keys = cards

    def dups(self) -> CountsValuesView:
        return self._data.values()

    values = dups

    def items(self) -> CountsItemsView:
        return self._data.items()

    def __getitem__(self, outcome) -> int:
        return self._data[outcome]

    def __iter__(self) -> Iterator:
        return iter(self.keys())

    def __len__(self) -> int:
        return len(self._data)

    @cached_property
    def _deck_size(self) -> int:
        return sum(self._data.values())

    def deck_size(self) -> int:
        return self._deck_size

    def hand_size(self) -> int:
        return self._hand_size

    @cached_property
    def _denomiator(self) -> int:
        return icepool.math.comb(self.deck_size(), self.hand_size())

    def denominator(self) -> int:
        return self._denomiator

    def _is_resolvable(self) -> bool:
        return len(self.cards()) > 0

    def _pop_min(
        self, min_outcome
    ) -> Generator[tuple['OutcomeCountGen', int, int], None, None]:
        if not self.cards() or min_outcome != self.min_outcome():
            yield self, 0, 1
            return

        deck_count = self.dups()[0]

        min_count = max(0, deck_count + self.hand_size() - self.deck_size())
        max_count = min(deck_count, self.hand_size())
        for count in range(min_count, max_count + 1):
            popped_draw = Deck(
                self.cards()[1:],
                self.dups()[1:],
                hand_size=self.hand_size() - count,
            )
            weight = icepool.math.comb(deck_count, count)
            yield popped_draw, count, weight

    def _pop_max(
        self, max_outcome
    ) -> Generator[tuple['OutcomeCountGen', int, int], None, None]:
        if not self.cards() or max_outcome != self.max_outcome():
            yield self, 0, 1
            return

        deck_count = self.dups()[-1]

        min_count = max(0, deck_count + self.hand_size() - self.deck_size())
        max_count = min(deck_count, self.hand_size())
        for count in range(min_count, max_count + 1):
            popped_draw = Deck(self.cards()[:-1],
                               self.dups()[:-1],
                               hand_size=self.hand_size() - count)
            weight = icepool.math.comb(deck_count, count)
            yield popped_draw, count, weight

    def _estimate_direction_costs(self) -> tuple[int, int]:
        result = len(self.cards()) * self.hand_size()
        return result, result

    @cached_property
    def _key_tuple(self) -> tuple:
        return (Deck,) + tuple(self.items()) + (self.hand_size(),)

    def __eq__(self, other) -> bool:
        if not isinstance(other, Deck):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash


empty_deck = Deck([], hand_size=0)
