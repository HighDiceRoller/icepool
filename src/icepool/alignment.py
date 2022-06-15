__docformat__ = 'google'

from icepool.gen import OutcomeCountGen

from functools import cached_property

from typing import Generator
from collections.abc import Collection, Sequence


class Alignment(OutcomeCountGen):
    """A generator that only outputs 0 counts with weight 1."""

    def __init__(self, outcomes: Collection):
        self._outcomes = tuple(sorted(outcomes))

    def outcomes(self) -> Sequence:
        return self._outcomes

    def _is_resolvable(self) -> bool:
        return True

    def _pop_min(
            self,
            min_outcome) -> Generator[tuple['Alignment', int, int], None, None]:
        """`Alignment` only outputs 0 counts with weight 1."""
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, 0, 1
        else:
            yield Alignment(self.outcomes()[1:]), 0, 1

    def _pop_max(
            self,
            max_outcome) -> Generator[tuple['Alignment', int, int], None, None]:
        """`Alignment` only outputs 0 counts with weight 1."""
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, 0, 1
        else:
            yield Alignment(self.outcomes()[:-1]), 0, 1

    def _estimate_direction_costs(self) -> tuple[int, int]:
        result = len(self.outcomes())
        return result, result

    def __eq__(self, other) -> bool:
        if not isinstance(other, Alignment):
            return False
        return self._outcomes == other._outcomes

    @cached_property
    def _hash(self) -> int:
        return hash(self._outcomes)

    def __hash__(self) -> int:
        return self._hash
