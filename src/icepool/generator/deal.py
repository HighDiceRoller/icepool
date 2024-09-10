__docformat__ = 'google'

import icepool
from icepool.generator.keep import KeepGenerator, pop_max_from_keep_tuple, pop_min_from_keep_tuple
from icepool.collection.counts import CountsKeysView
from icepool.generator.multiset_generator import InitialMultisetGenerator, NextMultisetGenerator
import icepool.generator.pop_order
from icepool.generator.pop_order import PopOrderReason

from functools import cached_property

from icepool.typing import Order, T
from typing import Hashable


class Deal(KeepGenerator[T]):
    """Represents an unordered deal of a single hand from a `Deck`."""

    _deck: 'icepool.Deck[T]'
    _hand_size: int

    def __init__(self, deck: 'icepool.Deck[T]', hand_size: int) -> None:
        """Constructor.

        For algorithmic reasons, you must pre-commit to the number of cards to
        deal.

        It is permissible to deal zero cards from an empty deck, but not all
        evaluators will handle this case, especially if they depend on the
        outcome type. Dealing zero cards from a non-empty deck does not have
        this issue.

        Args:
            deck: The `Deck` to deal from.
            hand_size: How many cards to deal.
        """
        if hand_size < 0:
            raise ValueError('hand_size cannot be negative.')
        if hand_size > deck.size():
            raise ValueError(
                'The number of cards dealt cannot exceed the size of the deck.'
            )
        self._deck = deck
        self._hand_size = hand_size
        self._keep_tuple = (1, ) * hand_size

    @classmethod
    def _new_raw(cls, deck: 'icepool.Deck[T]', hand_size: int,
                 keep_tuple: tuple[int, ...]) -> 'Deal[T]':
        self = super(Deal, cls).__new__(cls)
        self._deck = deck
        self._hand_size = hand_size
        self._keep_tuple = keep_tuple
        return self

    def _set_keep_tuple(self, keep_tuple: tuple[int, ...]) -> 'Deal[T]':
        return Deal._new_raw(self._deck, self._hand_size, keep_tuple)

    def deck(self) -> 'icepool.Deck[T]':
        """The `Deck` the cards are dealt from."""
        return self._deck

    def hand_sizes(self) -> tuple[int, ...]:
        """The number of cards dealt to each hand as a tuple."""
        return (self._hand_size, )

    def total_cards_dealt(self) -> int:
        """The total number of cards dealt."""
        return self._hand_size

    def outcomes(self) -> CountsKeysView[T]:
        """The outcomes of the `Deck` in ascending order.

        These are also the `keys` of the `Deck` as a `Mapping`.
        Prefer to use the name `outcomes`.
        """
        return self.deck().outcomes()

    def output_arity(self) -> int:
        return 1

    def _is_resolvable(self) -> bool:
        return len(self.outcomes()) > 0

    def denominator(self) -> int:
        return icepool.math.comb(self.deck().size(), self._hand_size)

    def _generate_initial(self) -> InitialMultisetGenerator:
        yield self, 1

    def _generate_min(self, min_outcome) -> NextMultisetGenerator:
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, (0, ), 1
            return

        popped_deck, deck_count = self.deck()._pop_min()

        min_count = max(0, deck_count + self._hand_size - self.deck().size())
        max_count = min(deck_count, self._hand_size)
        skip_weight = None
        for count in range(min_count, max_count + 1):
            popped_keep_tuple, result_count = pop_min_from_keep_tuple(
                self.keep_tuple(), count)
            popped_deal = Deal._new_raw(popped_deck, self._hand_size - count,
                                        popped_keep_tuple)
            weight = icepool.math.comb(deck_count, count)
            if not any(popped_keep_tuple):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight
                               or 0) + weight * popped_deal.denominator()
                continue
            yield popped_deal, (result_count, ), weight

        if skip_weight is not None:
            popped_deal = Deal._new_raw(popped_deck, 0, ())
            yield popped_deal, (sum(self.keep_tuple()), ), skip_weight

    def _generate_max(self, max_outcome) -> NextMultisetGenerator:
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, (0, ), 1
            return

        popped_deck, deck_count = self.deck()._pop_max()

        min_count = max(0, deck_count + self._hand_size - self.deck().size())
        max_count = min(deck_count, self._hand_size)
        skip_weight = None
        for count in range(min_count, max_count + 1):
            popped_keep_tuple, result_count = pop_max_from_keep_tuple(
                self.keep_tuple(), count)
            popped_deal = Deal._new_raw(popped_deck, self._hand_size - count,
                                        popped_keep_tuple)
            weight = icepool.math.comb(deck_count, count)
            if not any(popped_keep_tuple):
                # Dump all dice in exchange for the denominator.
                skip_weight = (skip_weight
                               or 0) + weight * popped_deal.denominator()
                continue
            yield popped_deal, (result_count, ), weight

        if skip_weight is not None:
            popped_deal = Deal._new_raw(popped_deck, 0, ())
            yield popped_deal, (sum(self.keep_tuple()), ), skip_weight

    def _preferred_pop_order(self) -> tuple[Order | None, PopOrderReason]:
        lo_skip, hi_skip = icepool.generator.pop_order.lo_hi_skip(
            self.keep_tuple())
        if lo_skip > hi_skip:
            return Order.Descending, PopOrderReason.KeepSkip
        if hi_skip > lo_skip:
            return Order.Ascending, PopOrderReason.KeepSkip

        return Order.Any, PopOrderReason.NoPreference

    @cached_property
    def _hash_key(self) -> Hashable:
        return Deal, self.deck(), self._hand_size, self._keep_tuple

    def __repr__(self) -> str:
        return type(
            self
        ).__qualname__ + f'({repr(self.deck())}, hand_size={self._hand_size})'

    def __str__(self) -> str:
        return type(
            self
        ).__qualname__ + f' of hand_size={self._hand_size} from deck:\n' + str(
            self.deck())
