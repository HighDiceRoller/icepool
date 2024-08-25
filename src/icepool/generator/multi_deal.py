__docformat__ = 'google'

from icepool.typing import Order, Qs, T

from typing import Any, Hashable, cast
import icepool
from icepool.collection.counts import CountsKeysView
from icepool.generator.multiset_generator import InitialMultisetGenerator, NextMultisetGenerator, MultisetGenerator
from icepool.math import iter_hypergeom
from icepool.generator.pop_order import PopOrderReason

from functools import cached_property
import math


class MultiDeal(MultisetGenerator[T, Qs]):
    """Represents an unordered deal of multiple hands from a `Deck`."""

    _deck: 'icepool.Deck[T]'
    _hand_sizes: Qs

    def __init__(self, deck: 'icepool.Deck[T]', *hand_sizes: int) -> None:
        """Constructor.

        For algorithmic reasons, you must pre-commit to the number of cards to
        deal for each hand.

        It is permissible to deal zero cards from an empty deck, but not all
        evaluators will handle this case, especially if they depend on the
        outcome type. Dealing zero cards from a non-empty deck does not have
        this issue.

        Args:
            deck: The `Deck` to deal from.
            *hand_sizes: How many cards to deal. If multiple `hand_sizes` are
                provided, `MultisetEvaluator.next_state` will recieve one count
                per hand in order. Try to keep the number of hands to a minimum
                as this can be computationally intensive.
        """
        if any(hand < 0 for hand in hand_sizes):
            raise ValueError('hand_sizes cannot be negative.')
        self._deck = deck
        self._hand_sizes = cast(Qs, hand_sizes)
        if self.total_cards_dealt() > self.deck().size():
            raise ValueError(
                'The total number of cards dealt cannot exceed the size of the deck.'
            )

    @classmethod
    def _new_raw(cls, deck: 'icepool.Deck[T]',
                 hand_sizes: Qs) -> 'MultiDeal[T, Qs]':
        self = super(MultiDeal, cls).__new__(cls)
        self._deck = deck
        self._hand_sizes = hand_sizes
        return self

    def deck(self) -> 'icepool.Deck[T]':
        """The `Deck` the cards are dealt from."""
        return self._deck

    def hand_sizes(self) -> Qs:
        """The number of cards dealt to each hand as a tuple."""
        return self._hand_sizes

    def total_cards_dealt(self) -> int:
        """The total number of cards dealt."""
        return sum(self.hand_sizes())

    def outcomes(self) -> CountsKeysView[T]:
        """The outcomes of the `Deck` in ascending order.

        These are also the `keys` of the `Deck` as a `Mapping`.
        Prefer to use the name `outcomes`.
        """
        return self.deck().outcomes()

    def output_arity(self) -> int:
        return len(self._hand_sizes)

    def _is_resolvable(self) -> bool:
        return len(self.outcomes()) > 0

    @cached_property
    def _denomiator(self) -> int:
        d_total = icepool.math.comb(self.deck().size(),
                                    self.total_cards_dealt())
        d_split = math.prod(
            icepool.math.comb(self.total_cards_dealt(), h)
            for h in self.hand_sizes()[1:])
        return d_total * d_split

    def denominator(self) -> int:
        return self._denomiator

    def _generate_initial(self) -> InitialMultisetGenerator:
        yield self, 1

    def _generate_common(self, popped_deck: 'icepool.Deck[T]',
                         deck_count: int) -> NextMultisetGenerator:
        """Common implementation for _generate_min and _generate_max."""
        min_count = max(
            0, deck_count + self.total_cards_dealt() - self.deck().size())
        max_count = min(deck_count, self.total_cards_dealt())
        for count_total in range(min_count, max_count + 1):
            weight_total = icepool.math.comb(deck_count, count_total)
            # The "deck" is the hand sizes.
            for counts, weight_split in iter_hypergeom(self.hand_sizes(),
                                                       count_total):
                popped_deal = MultiDeal._new_raw(
                    popped_deck,
                    tuple(h - c for h, c in zip(self.hand_sizes(), counts)))
                weight = weight_total * weight_split
                yield popped_deal, counts, weight

    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, (0, ), 1
            return

        popped_deck, deck_count = self.deck()._pop_min()

        yield from self._generate_common(popped_deck, deck_count)

    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, (0, ), 1
            return

        popped_deck, deck_count = self.deck()._pop_max()

        yield from self._generate_common(popped_deck, deck_count)

    def _preferred_pop_order(self) -> tuple[Order | None, PopOrderReason]:
        return Order.Any, PopOrderReason.NoPreference

    @cached_property
    def _hash_key(self) -> Hashable:
        return MultiDeal, self.deck(), self.hand_sizes()

    def __repr__(self) -> str:
        return type(
            self
        ).__qualname__ + f'({repr(self.deck())}, hand_sizes={self.hand_sizes()})'

    def __str__(self) -> str:
        return type(
            self
        ).__qualname__ + f' of hand_sizes={self.hand_sizes()} from deck:\n' + str(
            self.deck())
