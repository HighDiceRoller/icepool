__docformat__ = 'google'

import icepool
from icepool.collection.counts import CountsKeysView
from icepool.expression.multiset_tuple_expression import IntTupleOut
from icepool.generator.multiset_tuple_generator import MultisetTupleGenerator, MultisetTupleSource
from icepool.math import iter_hypergeom
from icepool.order import Order, OrderReason

import math
import itertools
from functools import cached_property

from icepool.typing import T

from typing import Hashable, Iterable, Iterator, cast


class MultiDeal(MultisetTupleGenerator[T, IntTupleOut]):
    """Represents an deal of multiple hands from a `Deck`.
    
    The cards within each hand are in sorted order. Furthermore, hands may be
    organized into groups in which the hands are initially indistinguishable.
    """

    _deck: 'icepool.Deck[T]'
    # An ordered tuple of hand groups.
    # Each group is designated by (hand_size, hand_count).
    _hand_groups: tuple[tuple[int, int], ...]

    def __init__(self, deck: 'icepool.Deck[T]',
                 hand_groups: tuple[tuple[int, int], ...]) -> None:
        """Constructor.

        For algorithmic reasons, you must pre-commit to the number of cards to
        deal for each hand.

        It is permissible to deal zero cards from an empty deck, but not all
        evaluators will handle this case, especially if they depend on the
        outcome type. Dealing zero cards from a non-empty deck does not have
        this issue.

        Args:
            deck: The `Deck` to deal from.
            hand_groups: An ordered tuple of hand groups.
                Each group is designated by (hand_size, hand_count) with the
                hands of each group being arbitrarily ordered.
                The resulting counts are produced in a flat tuple.
        """
        self._deck = deck
        self._hand_groups = hand_groups
        if self.total_cards_dealt() > self.deck().size():
            raise ValueError(
                'The total number of cards dealt cannot exceed the size of the deck.'
            )

    @classmethod
    def _new_raw(
        cls, deck: 'icepool.Deck[T]',
        hand_sizes: tuple[tuple[int, int],
                          ...]) -> 'MultiDeal[T, IntTupleOut]':
        self = super(MultiDeal, cls).__new__(cls)
        self._deck = deck
        self._hand_groups = hand_sizes
        return self

    def deck(self) -> 'icepool.Deck[T]':
        """The `Deck` the cards are dealt from."""
        return self._deck

    def hand_sizes(self) -> IntTupleOut:
        """The number of cards dealt to each hand as a tuple."""
        return cast(
            IntTupleOut,
            tuple(
                itertools.chain.from_iterable(
                    (hand_size, ) * group_size
                    for hand_size, group_size in self._hand_groups)))

    def total_cards_dealt(self) -> int:
        """The total number of cards dealt."""
        return sum(hand_size * group_size
                   for hand_size, group_size in self._hand_groups)

    def outcomes(self) -> CountsKeysView[T]:
        """The outcomes of the `Deck` in ascending order.

        These are also the `keys` of the `Deck` as a `Mapping`.
        Prefer to use the name `outcomes`.
        """
        return self.deck().outcomes()

    def __len__(self) -> int:
        return sum(group_size for _, group_size in self._hand_groups)

    @cached_property
    def _denominator(self) -> int:
        d_total = icepool.math.comb(self.deck().size(),
                                    self.total_cards_dealt())
        d_split = math.prod(
            icepool.math.comb(self.total_cards_dealt(), h)
            for h in self.hand_sizes()[1:])
        return d_total * d_split

    def denominator(self) -> int:
        return self._denominator

    def _make_source(self) -> 'MultisetTupleSource[T, IntTupleOut]':
        return MultiDealSource(self._deck, self._hand_groups)

    @property
    def hash_key(self) -> Hashable:
        return MultiDeal, self._deck, self._hand_groups

    def __repr__(self) -> str:
        return type(
            self
        ).__qualname__ + f'({repr(self.deck())}, hand_groups={self._hand_groups})'

    def __str__(self) -> str:
        return type(
            self
        ).__qualname__ + f' of hand_groups={self._hand_groups} from deck:\n' + str(
            self.deck())


class MultiDealSource(MultisetTupleSource[T, IntTupleOut]):

    def __init__(self, deck: 'icepool.Deck[T]',
                 hand_groups: tuple[tuple[int, int], ...]):
        self.deck = deck
        self.hand_groups = hand_groups

    def outcomes(self):
        return self.deck.outcomes()

    def size(self):
        return self.hand_sizes()

    def pop(self, order: Order, outcome: T):
        if not self.outcomes():
            yield self, (0, ) * self.hand_count(), 1
            return

        if order > 0:
            pop_outcome = self.outcomes()[0]
            popped_deck, deck_count = self.deck._pop_min()
        else:
            pop_outcome = self.outcomes()[-1]
            popped_deck, deck_count = self.deck._pop_max()

        if pop_outcome != outcome:
            yield self, (0, ) * self.hand_count(), 1
            return

        min_count = max(
            0, deck_count + self.total_cards_dealt() - self.deck.size())
        max_count = min(deck_count, self.total_cards_dealt())
        for count_total in range(min_count, max_count + 1):
            weight_total = icepool.math.comb(deck_count, count_total)
            # The "deck" assigns the cards of the current outcome to hands.
            skip_weight = None
            for raw_counts, weight_split in iter_hypergeom(
                    self.hand_sizes(), count_total):
                pos = 0
                counts = list(raw_counts)
                next_hand_groups: list[tuple[int, int]] = []
                for hand_size, group_size in self.hand_groups:
                    counts[pos:pos + group_size] = sorted(
                        raw_counts[pos:pos + group_size], reverse=True)
                    for count, next_group_counts in itertools.groupby(
                            counts[pos:pos + group_size]):
                        next_group_size = len(list(next_group_counts))
                        if count == hand_size:
                            next_hand_groups.extend(
                                ((0, 1), ) * next_group_size)
                        else:
                            next_hand_groups.append(
                                (hand_size - count, next_group_size))
                    pos += group_size
                popped_source = MultiDealSource[T, IntTupleOut](
                    popped_deck, tuple(next_hand_groups))
                weight = weight_total * weight_split
                if not any(hand_size for hand_size, _ in next_hand_groups):
                    skip_weight = (skip_weight or
                                   0) + weight * popped_source.denominator()
                    continue
                yield popped_source, tuple(counts), weight

        if skip_weight is not None:
            skip_source = MultiDealSource[T, IntTupleOut](
                popped_deck, ((0, 1), ) * self.hand_count())
            yield skip_source, self.hand_sizes(), skip_weight

    def order_preference(self) -> tuple[Order, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    @property
    def hash_key(self):
        return MultiDealSource, self.deck, self.hand_groups

    @cached_property
    def _denominator(self) -> int:
        d_total = icepool.math.comb(self.deck.size(), self.total_cards_dealt())
        d_split = math.prod(
            icepool.math.comb(self.total_cards_dealt(), h)
            for h in self.hand_sizes()[1:])
        return d_total * d_split

    def denominator(self) -> int:
        return self._denominator

    def hand_sizes(self) -> IntTupleOut:
        """The number of cards dealt to each hand as a tuple."""
        return cast(
            IntTupleOut,
            tuple(
                itertools.chain.from_iterable(
                    (hand_size, ) * group_size
                    for hand_size, group_size in self.hand_groups)))

    def hand_count(self) -> int:
        return sum(group_size for _, group_size in self.hand_groups)

    def total_cards_dealt(self) -> int:
        """The total number of cards dealt."""
        return sum(hand_size * group_size
                   for hand_size, group_size in self.hand_groups)

    def is_resolvable(self) -> bool:
        return len(self.outcomes()) != 0
