"""Binary operators between a generator on the left and an integer on the right."""

__docformat__ = 'google'

from icepool.generator.outcome_count_generator import NextOutcomeCountGenerator, OutcomeCountGenerator
from icepool.typing import Outcome, MultisetBinaryIntOperationStr

from abc import abstractmethod
from functools import cached_property

from typing import Sequence, TypeVar

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""Type variable representing the outcome type."""

Qints_co = TypeVar('Qints_co', bound=tuple[int, ...], covariant=True)
"""Type variable representing the counts type, which is a tuple of `int`s.

In this future this may be replaced with a TypeVarTuple."""

class AdjustCountsGenerator(OutcomeCountGenerator[T_co, Qints_co]):
    """Adjusts counts of a generator.

    If the generator produces multiple counts, each count will be affected
    individually.
    """

    def __init__(self, inner: OutcomeCountGenerator[T_co, Qints_co], constant: int):
        self._inner = inner
        self._constant = constant

    @classmethod
    def new_by_name(self, name: MultisetBinaryIntOperationStr, inner: OutcomeCountGenerator[T_co, Qints_co],
                 constant: int) -> 'AdjustCountsGenerator[T_co, Qints_co]':
        match name:
            case '*': return MultiplyCountsGenerator(inner, constant)
            case '//': return FloorDivCountsGenerator(inner, constant)
            case _: raise ValueError(f'Invalid operator {name}.')

    @staticmethod
    @abstractmethod
    def adjust_count(count: int, constant: int) -> int:
        """Adjusts the count."""

    def outcomes(self) -> Sequence[T_co]:
        return self._inner.outcomes()

    def counts_len(self) -> int:
        return self._inner.counts_len()

    def _is_resolvable(self) -> bool:
        return self._inner._is_resolvable()

    def _generate_min(self, min_outcome) -> NextOutcomeCountGenerator:
        for gen, counts, weight in self._inner._generate_min(min_outcome):
            next_counts = tuple(self.adjust_count(count, self._constant) for count in counts)
            next_generator = self.__class__(gen, self._constant)
            yield next_generator, next_counts, weight

    def _generate_max(self, max_outcome) -> NextOutcomeCountGenerator:
        for gen, counts, weight in self._inner._generate_max(max_outcome):
            next_counts = tuple(self.adjust_count(count, self._constant) for count in counts)
            next_generator = self.__class__(gen, self._constant)
            yield next_generator, next_counts, weight

    def _estimate_order_costs(self) -> tuple[int, int]:
        return self._inner._estimate_order_costs()

    def denominator(self) -> int:
        return self._inner.denominator()

    @cached_property
    def _key_tuple(self) -> tuple:
        return self.__class__, self._inner

    def equals(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self._key_tuple == other._key_tuple

    @cached_property
    def _hash(self) -> int:
        return hash(self._key_tuple)

    def __hash__(self) -> int:
        return self._hash

class MultiplyCountsGenerator(AdjustCountsGenerator[T_co, Qints_co]):
    """Multiplies all counts by the constant."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        return count * constant

class FloorDivCountsGenerator(AdjustCountsGenerator[T_co, Qints_co]):
    """Divides all counts by the constant, rounding down."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        return count // constant

class FilterCountsGenerator(AdjustCountsGenerator[T_co, Qints_co]):
    """Counts below a certain value are treated as zero."""
    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        if count < constant:
            return 0
        else:
            return count

class UniqueGenerator(AdjustCountsGenerator[T_co, Qints_co]):
    """Limits the count produced by each outcome."""
    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        return min(count, constant)
