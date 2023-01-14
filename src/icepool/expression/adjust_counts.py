__docformat__ = 'google'

from typing import Hashable
from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Order, Outcome

from abc import abstractmethod
from functools import cached_property


class AdjustCountsExpression(MultisetExpression):

    def __init__(self, inner: MultisetExpression, constant: int) -> None:
        self._inner = inner
        self._constant = constant

    @staticmethod
    @abstractmethod
    def adjust_count(count: int, constant: int) -> int:
        """Adjusts the count."""

    def next_state(self, state, outcome: Outcome,
                   *counts: int) -> tuple[Hashable, int]:
        count = self.adjust_count(counts[0], self._constant)
        return state, count

    def order(self) -> Order:
        return self._inner.order()

    def shift_variables(self, shift: int) -> MultisetExpression:
        return self.__class__(self._inner.shift_variables(shift),
                              self._constant)

    @property
    def arity(self) -> int:
        return self._inner.arity

    @cached_property
    def _key_tuple(self) -> tuple[Hashable, ...]:
        return type(self), self._inner, self._constant


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
