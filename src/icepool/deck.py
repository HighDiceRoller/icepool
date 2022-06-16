__docformat__ = 'google'

import icepool
import icepool.math
import icepool.creation_args
from icepool.counts import Counts, CountsKeysView, CountsValuesView, CountsItemsView
from icepool.gen import OutcomeCountGen

from functools import cached_property

from typing import Any, Generator, Iterator
from collections.abc import Mapping, Sequence


class Deck(OutcomeCountGen, Mapping[Any, int]):
    """EXPERIMENTAL: Represents drawing a hand from a deck.

    In other words, this is sampling without replacement.
    """

    _data: Counts
    _draws: int

    def __new__(cls,
                outcomes: Mapping[Any, int] | Sequence,
                times: Sequence[int] | int = 1,
                *,
                draws: int) -> 'Deck':
        """Constructor for a deck.

        Args:
            outcomes: The cards of the deck. This can be one of the following:
                * A `Mapping` from outcomes to dups.
                * A sequence of outcomes.

                Note that `Die` and `Deck` both count as `Mapping`s.

                Each card may be one of the following:
                * A `Mapping` from outcomes to dups.
                    The outcomes of the `Mapping` will be "flattened" into the
                    result. This option will be taken in preference to treating
                    the `Mapping` itself as an outcome even if the `Mapping`
                    itself is hashable and totally orderable. This means that
                    `Die` and `Deck` will never be outcomes.
                * A tuple of outcomes.
                    Any tuple elements that are `Mapping`s will expand the
                    tuple according to their independent joint distribution.
                    For example, `(d6, d6)` will expand to 36 ordered tuples
                    with dup 1 each. Use this carefully since it may create a
                    large number of outcomes.
                * Anything else will be treated as a single outcome.
                    Each outcome must be hashable, and the
                    set of outcomes must be totally orderable (after expansion).
                    The same outcome can appear multiple times, in which case
                    the corresponding dups will be accumulated.
            times: Multiplies the number of times each element of `outcomes`
                will be put into the deck.
                `times` can either be a sequence of the same length as
                `outcomes` or a single `int` to apply to all elements of
                `outcomes`.
        """
        if isinstance(outcomes, Deck):
            if times == 1:
                return outcomes
            else:
                outcomes = outcomes._data

        outcomes, times = icepool.creation_args.itemize(outcomes, times)

        if len(outcomes) == 1 and times[0] == 1 and isinstance(
                outcomes[0], Deck):
            return outcomes[0]

        data = icepool.creation_args.expand_args_for_deck(outcomes, times)
        return Deck._new_deck(data, draws)

    @classmethod
    def _new_deck(cls, data: Counts, draws: int) -> 'Deck':
        """Creates a new deck using already-processed arguments.

        Args:
            data: At this point, this is a Counts.
            draws
        """
        self = super(Deck, cls).__new__(cls)
        self._data = data
        self._draws = draws
        if self.draws() > self.deck_size():
            raise ValueError('draws cannot exceed deck_size.')
        return self

    def outcomes(self) -> CountsKeysView:
        """The outcomes of the deck in sorted order.

        These are also the `keys` of the deck as a `Mapping`.
        Prefer to use the name `outcomes`.
        """
        return self._data.keys()

    keys = outcomes

    def dups(self) -> CountsValuesView:
        """The dups of the deck in outcome order.

        These are also the `values` of the deck as a `Mapping`.
        Prefer to use the name `dups`.
        """
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

    def draws(self) -> int:
        return self._draws

    @cached_property
    def _denomiator(self) -> int:
        return icepool.math.comb(self.deck_size(), self.draws())

    def denominator(self) -> int:
        return self._denomiator

    def _is_resolvable(self) -> bool:
        return len(self.outcomes()) > 0

    def _pop_min(
        self, min_outcome
    ) -> Generator[tuple['OutcomeCountGen', int, int], None, None]:
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, 0, 1
            return

        deck_count = self.dups()[0]

        min_count = max(0, deck_count + self.draws() - self.deck_size())
        max_count = min(deck_count, self.draws())
        for count in range(min_count, max_count + 1):
            popped_deck = Deck._new_deck(self._data.remove_min(),
                                         draws=self.draws() - count)
            weight = icepool.math.comb(deck_count, count)
            yield popped_deck, count, weight

    def _pop_max(
        self, max_outcome
    ) -> Generator[tuple['OutcomeCountGen', int, int], None, None]:
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, 0, 1
            return

        deck_count = self.dups()[-1]

        min_count = max(0, deck_count + self.draws() - self.deck_size())
        max_count = min(deck_count, self.draws())
        for count in range(min_count, max_count + 1):
            popped_deck = Deck._new_deck(self._data.remove_max(),
                                         draws=self.draws() - count)
            weight = icepool.math.comb(deck_count, count)
            yield popped_deck, count, weight

    def _estimate_direction_costs(self) -> tuple[int, int]:
        result = len(self.outcomes()) * self.draws()
        return result, result

    @cached_property
    def _key_tuple(self) -> tuple:
        return Deck, tuple(self.items()), self.draws()

    def __eq__(self, other) -> bool:
        if not isinstance(other, Deck):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash


empty_deck = Deck([], draws=0)
