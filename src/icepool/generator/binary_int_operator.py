"""Binary operators between a generator on the left and an integer on the right."""

__docformat__ = 'google'

from icepool.generator.outcome_count_generator import NextOutcomeCountGenerator, OutcomeCountGenerator
from icepool.typing import Outcome, MultisetBinaryIntOperationStr

import itertools
from abc import abstractmethod
from functools import cached_property

from typing import Literal, Sequence, TypeVar

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""Type variable representing the outcome type."""


class BinaryIntOperatorGenerator(OutcomeCountGenerator[T_co]):

    def __init__(self, inner: OutcomeCountGenerator[T_co], integer: int):
        self._inner = inner
        self._integer = integer

    @classmethod
    def new_by_name(self, op: MultisetBinaryIntOperationStr, inner: OutcomeCountGenerator[T_co],
                 integer: int) -> 'BinaryIntOperatorGenerator[T_co]':
        match op:
            case '*': return MultisetMultiplyGenerator(inner, integer)
            case '//': return MultisetFloorDivideGenerator(inner, integer)
            case _: raise ValueError(f'Invalid operator {op}.')

    @staticmethod
    @abstractmethod
    def adjust_count(count: int, integer: int) -> int:
        """Adjusts the count according to the operator."""

    def outcomes(self) -> Sequence[T_co]:
        return self._inner.outcomes()

    def counts_len(self) -> int:
        """The number of counts generated. Must be constant."""
        return self._inner.counts_len()

    def _is_resolvable(self) -> bool:
        return self._inner._is_resolvable()

    def _generate_min(self, min_outcome) -> NextOutcomeCountGenerator:
        for gen, counts, weight in self._inner._generate_min(min_outcome):
            next_counts = tuple(self.adjust_count(count, self._integer) for count in counts)
            next_generator = self.__class__(gen, self._integer)
            yield next_generator, next_counts, weight

    def _generate_max(self, max_outcome) -> NextOutcomeCountGenerator:
        for gen, counts, weight in self._inner._generate_max(max_outcome):
            next_counts = tuple(self.adjust_count(count, self._integer) for count in counts)
            next_generator = self.__class__(gen, self._integer)
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

class MultisetMultiplyGenerator(BinaryIntOperatorGenerator[T_co]):

    @staticmethod
    def adjust_count(count: int, integer: int) -> int:
        return count * integer

class MultisetFloorDivideGenerator(BinaryIntOperatorGenerator[T_co]):

    @staticmethod
    def adjust_count(count: int, integer: int) -> int:
        return count // integer
