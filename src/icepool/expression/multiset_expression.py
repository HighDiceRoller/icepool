__docformat__ = 'google'

import icepool.expression

from icepool.typing import Outcome

from abc import ABC, abstractmethod
from typing import Hashable


class MultisetExpression(Hashable, ABC):

    @abstractmethod
    def evaluate(self, outcome: Outcome, *counts: int) -> int:
        """Evaluate this expression, producing a single final count.

        Args:
            outcome: The current outcome.
            *counts: The original sequence of counts.
        """

    __call__ = evaluate

    # Binary operators.

    def __add__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(self, other)

    def __radd__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DisjointUnionExpression(other, self)

    def __sub__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DifferenceExpression(self, other)

    def __rsub__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.DifferenceExpression(other, self)

    def __and__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.IntersectionExpression(self, other)

    def __rand__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.IntersectionExpression(other, self)

    def __or__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.UnionExpression(self, other)

    def __ror__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.UnionExpression(other, self)

    def __xor__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(self, other)

    def __rxor__(self, other: 'MultisetExpression') -> 'MultisetExpression':
        if not isinstance(other, MultisetExpression):
            return NotImplemented
        return icepool.expression.SymmetricDifferenceExpression(other, self)

    # Adjust counts.

    def __mul__(self, other: int) -> 'MultisetExpression':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, other)

    # Commutable in this case.
    def __rmul__(self, other: int) -> 'MultisetExpression':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.MultiplyCountsExpression(self, other)

    def multiply_counts(self, constant: int, /) -> 'MultisetExpression':
        """Multiplies all counts by a constant.

        Same as `self * constant`.
        """
        return self * constant

    def __floordiv__(self, other: int) -> 'MultisetExpression':
        if not isinstance(other, int):
            return NotImplemented
        return icepool.expression.FloorDivCountsExpression(self, other)

    def divide_counts(self, constant: int, /) -> 'MultisetExpression':
        """Divides all counts by a constant (rounding down).

        Same as `self // constant`.
        """
        return self // constant

    def filter_counts(self, min_count: int) -> 'MultisetExpression':
        """Counts less than `min_count` are treated as zero.

        For example, `generator.filter_counts(2)` would only produce
        pairs and better.
        """
        return icepool.expression.FilterCountsExpression(self, min_count)

    def unique(self, max_count: int = 1) -> 'MultisetExpression':
        """Counts each outcome at most `max_count` times.

        For example, `generator.unique(2)` would count each outcome at most
        twice.
        """
        return icepool.expression.UniqueExpression(self, max_count)
