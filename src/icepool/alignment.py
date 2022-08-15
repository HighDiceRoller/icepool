__docformat__ = 'google'

from icepool.outcome_count_generator import OutcomeCountGenerator

from functools import cached_property

from typing import Collection, Generator, Sequence, TypeAlias

AlignmentGenerator: TypeAlias = Generator[tuple['Alignment', Sequence[int],
                                                int], None, None]


class Alignment(OutcomeCountGenerator):
    """A generator that only outputs 0 counts with weight 1."""

    def __init__(self, outcomes: Collection):
        self._outcomes = tuple(sorted(outcomes))

    def outcomes(self) -> Sequence:
        return self._outcomes

    def _is_resolvable(self) -> bool:
        return True

    def _generate_min(self, min_outcome) -> AlignmentGenerator:
        """`Alignment` only outputs 0 counts with weight 1."""
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, (0,), 1
        else:
            yield Alignment(self.outcomes()[1:]), (0,), 1

    def _generate_max(self, max_outcome) -> AlignmentGenerator:
        """`Alignment` only outputs 0 counts with weight 1."""
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, (0,), 1
        else:
            yield Alignment(self.outcomes()[:-1]), (0,), 1

    def _estimate_order_costs(self) -> tuple[int, int]:
        result = len(self.outcomes())
        return result, result

    def denominator(self) -> int:
        return 0

    def __eq__(self, other) -> bool:
        if not isinstance(other, Alignment):
            return False
        return self._outcomes == other._outcomes

    @cached_property
    def _hash(self) -> int:
        return hash(self._outcomes)

    def __hash__(self) -> int:
        return self._hash
