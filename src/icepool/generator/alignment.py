__docformat__ = 'google'

from icepool.expression.base import MultisetExpressionBase
from icepool.generator.multiset_generator import MultisetGenerator
from icepool.order import Order, OrderReason

from functools import cached_property

from icepool.typing import T
from typing import Collection, Hashable, Iterator, Sequence, TypeAlias

InitialAlignmentGenerator: TypeAlias = Iterator[tuple['Alignment', int]]

AlignmentGenerator: TypeAlias = Iterator[tuple['Alignment', None, int]]


class Alignment(MultisetExpressionBase[T, None]):
    """A generator that only outputs `None` counts.

    This can be used to enforce that certain outcomes are seen without otherwise
    affecting a multiset evaluation.
    """
    _children = ()

    def __init__(self, outcomes: Collection[T]):
        self._outcomes = tuple(sorted(outcomes))

    @property
    def _variable_type(self):
        return Alignment

    def outcomes(self) -> Sequence[T]:
        return self._outcomes

    def _is_resolvable(self) -> bool:
        return True

    def _generate_initial(self) -> InitialAlignmentGenerator:
        yield self, 1

    def _generate_min(self,
                      min_outcome) -> Iterator[tuple['Alignment', None, int]]:
        """`Alignment` only outputs 0 counts with weight 1."""
        if not self.outcomes() or min_outcome != self.min_outcome():
            yield self, None, 1
        else:
            yield Alignment(self.outcomes()[1:]), None, 1

    def _generate_max(self,
                      max_outcome) -> Iterator[tuple['Alignment', None, int]]:
        """`Alignment` only outputs 0 counts with weight 1."""
        if not self.outcomes() or max_outcome != self.max_outcome():
            yield self, None, 1
        else:
            yield Alignment(self.outcomes()[:-1]), None, 1

    def has_free_variables(self) -> bool:
        return False

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    @cached_property
    def _local_hash_key(self) -> Hashable:
        return Alignment, self._outcomes

    def _unbind(
        self,
        bound_inputs: 'list[MultisetExpressionBase]' = []
    ) -> 'MultisetExpressionBase':
        raise RuntimeError('Alignment should not have _unbind called.')

    def _apply_variables(self, outcome: T, bound_counts: tuple[int, ...],
                         free_counts: tuple[int, ...]):
        raise RuntimeError(
            'Alignment should not have _apply_variables called.')
