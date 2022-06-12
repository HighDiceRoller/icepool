__docformat__ = 'google'

import icepool
import icepool.math
from icepool.generator import OutcomeCountGen
from icepool.outcome_args import expand_outcome_args

from functools import cached_property

from typing import Any, Generator
from collections.abc import Sequence


class CardDraw(OutcomeCountGen):
    """EXPERIMENTAL: Represents drawing a hand from a deck.

    In other words, this is sampling without replacement.
    """

    def __init__(self,
                 *deck,
                 hand_size: int,
                 dups: Sequence[int] | None = None,
                 denominator_method: str = 'lcm'):
        self._deck = expand_outcome_args(*deck,
                                         counts=dups,
                                         denominator_method=denominator_method)
        self._hand_size = hand_size
        if self.hand_size() > self.deck_size():
            raise ValueError('hand_size cannot exceed deck_size.')

    def outcomes(self) -> Sequence:
        return self._deck.keys()

    def dups(self) -> Sequence[int]:
        return self._deck.values()

    def items(self) -> Sequence[tuple[Any, int]]:
        return self._deck.items()

    @cached_property
    def _deck_size(self) -> int:
        return sum(self._deck.values())

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
        return len(self.outcomes()) > 0

    def _pop_min(
        self, min_outcome
    ) -> Generator[tuple['OutcomeCountGen', int, int], None, None]:
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, 0, 1
            return

        deck_count = self.dups()[0]

        min_count = max(0, deck_count + self.hand_size() - self.deck_size())
        max_count = min(deck_count, self.hand_size())
        for count in range(min_count, max_count + 1):
            popped_draw = CardDraw(*self.outcomes()[1:],
                                   hand_size=self.hand_size() - count,
                                   dups=self.dups()[1:])
            weight = icepool.math.comb(deck_count, count)
            yield popped_draw, count, weight

    def _pop_max(
        self, max_outcome
    ) -> Generator[tuple['OutcomeCountGen', int, int], None, None]:
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, 0, 1
            return

        deck_count = self.dups()[-1]

        min_count = max(0, deck_count + self.hand_size() - self.deck_size())
        max_count = min(deck_count, self.hand_size())
        for count in range(min_count, max_count + 1):
            popped_draw = CardDraw(*self.outcomes()[:-1],
                                   hand_size=self.hand_size() - count,
                                   dups=self.dups()[:-1])
            weight = icepool.math.comb(deck_count, count)
            yield popped_draw, count, weight

    def _estimate_direction_costs(self) -> tuple[int, int]:
        result = len(self.outcomes()) * self.hand_size()
        return result, result

    @cached_property
    def _key_tuple(self) -> tuple:
        return ('CardDraw',) + tuple(self.items()) + (self.hand_size(),)

    def __eq__(self, other) -> bool:
        if not isinstance(other, CardDraw):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash


empty_card_draw = CardDraw(hand_size=0)