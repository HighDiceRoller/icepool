__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

from abc import abstractmethod
from functools import cached_property

from icepool.typing import Order, Outcome, T_contra
from typing import Hashable, Sequence


class AdjustCountsExpression(MultisetExpression[T_contra]):

    def __init__(self, inner: MultisetExpression[T_contra],
                 constant: int) -> None:
        self._validate_output_arity(inner)
        self._inner = inner
        self._constant = constant

    @staticmethod
    @abstractmethod
    def adjust_count(count: int, constant: int) -> int:
        """Adjusts the count."""

    def _next_state(self, state, outcome: T_contra, bound_counts: tuple[int,
                                                                        ...],
                    counts: tuple[int, ...]) -> tuple[Hashable, int]:
        state, count = self._inner._next_state(state, outcome, bound_counts,
                                               counts)
        count = self.adjust_count(count, self._constant)
        return state, count

    def _order(self) -> Order:
        return self._inner._order()

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._inner._bound_generators()

    def _arity(self) -> int:
        return self._inner._arity()


class MultiplyCountsExpression(AdjustCountsExpression):
    """Multiplies all counts by the constant."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        return count * constant

    def __str__(self) -> str:
        return f'({self._inner} * {self._constant})'


class FloorDivCountsExpression(AdjustCountsExpression):
    """Divides all counts by the constant, rounding down."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        return count // constant

    def __str__(self) -> str:
        return f'({self._inner} // {self._constant})'


class FilterCountsExpression(AdjustCountsExpression):
    """Counts below a certain value are treated as zero."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        if count < constant:
            return 0
        else:
            return count

    def __str__(self) -> str:
        return f'{self._inner}.filter_counts({self._constant})'


class UniqueExpression(AdjustCountsExpression):
    """Limits the count produced by each outcome."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        return min(count, constant)

    def __str__(self) -> str:
        if self._constant == 1:
            return f'{self._inner}.unique()'
        else:
            return f'{self._inner}.unique({self._constant})'
