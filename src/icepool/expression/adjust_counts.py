__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import Outcome

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

    def evaluate_counts(self, outcome: Outcome, *counts: int) -> int:
        inner = self._inner.evaluate_counts(outcome, *counts)
        return self.adjust_count(inner, self._constant)


class MultiplyCountsExpression(AdjustCountsExpression):
    """Multiplies all counts by the constant."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        return count * constant


class FloorDivCountsExpression(AdjustCountsExpression):
    """Divides all counts by the constant, rounding down."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        return count // constant


class FilterCountsExpression(AdjustCountsExpression):
    """Counts below a certain value are treated as zero."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        if count < constant:
            return 0
        else:
            return count


class UniqueExpression(AdjustCountsExpression):
    """Limits the count produced by each outcome."""

    @staticmethod
    def adjust_count(count: int, constant: int) -> int:
        return min(count, constant)