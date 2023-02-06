__docformat__ = 'google'

from icepool.generator.multiset_generator import MultisetGenerator
from icepool.typing import Outcome, T

from functools import cached_property

from typing import Collection, Hashable, Iterator, Sequence, TypeAlias

AlignmentGenerator: TypeAlias = Iterator[tuple['Alignment', Sequence[int], int]]


class Alignment(MultisetGenerator[T, tuple[()]]):
    """A generator that does not output any counts.

    This can be used to enforce that certain outcomes are seen without otherwise
    affecting a multiset evaluation.
    """

    def __init__(self, outcomes: Collection[T]):
        self._outcomes = tuple(sorted(outcomes))

    def outcomes(self) -> Sequence[T]:
        return self._outcomes

    def output_arity(self) -> int:
        return 0

    def _is_resolvable(self) -> bool:
        return True

    def _generate_min(self, min_outcome) -> AlignmentGenerator:
        """`Alignment` only outputs 0 counts with weight 1."""
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, (0,), 1
        else:
            yield Alignment(self.outcomes()[1:]), (), 1

    def _generate_max(self, max_outcome) -> AlignmentGenerator:
        """`Alignment` only outputs 0 counts with weight 1."""
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, (0,), 1
        else:
            yield Alignment(self.outcomes()[:-1]), (), 1

    def _estimate_order_costs(self) -> tuple[int, int]:
        result = len(self.outcomes())
        return result, result

    def denominator(self) -> int:
        return 0

    @cached_property
    def _key_tuple(self) -> tuple[Hashable, ...]:
        return Alignment, self._outcomes
