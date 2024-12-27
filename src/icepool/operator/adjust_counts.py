__docformat__ = 'google'

import icepool

from icepool.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator
from icepool.order import Order, OrderReason

import operator
from abc import abstractmethod
from functools import cached_property, reduce

from typing import Callable, Hashable, Iterable, Literal
from icepool.typing import T


class MultisetMapCounts(MultisetOperator[T]):
    """Maps outcomes and counts to new counts."""

    _function: Callable[..., int]

    def __init__(self, *children: MultisetExpression[T],
                 function: Callable[..., int]) -> None:
        """Constructor.

        Args:
            children: The children expression(s).
            function: A function that takes `outcome, *counts` and produces a
                combined count.
        """
        self._children = children
        self._function = function

    def _copy(
        self, new_children: 'tuple[MultisetExpression[T], ...]'
    ) -> 'MultisetExpression[T]':
        return MultisetMapCounts(*new_children, function=self._function)

    def _transform_next(
            self, new_children: 'tuple[MultisetExpression[T], ...]',
            outcome: T,
            counts: 'tuple[int, ...]') -> 'tuple[MultisetExpression[T], int]':
        count = self._function(outcome, *counts)
        return MultisetMapCounts(*new_children, function=self._function), count

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    @property
    def _local_hash_key(self) -> Hashable:
        return MultisetMapCounts, self._function


class MultisetCountOperator(MultisetOperator[T]):

    def __init__(self, child: MultisetExpression[T], /, *,
                 constant: int) -> None:
        self._children = (child, )
        self._constant = constant

    @abstractmethod
    def operator(self, count: int) -> int:
        """Operation to apply to the counts."""

    def _copy(
        self, new_children: 'tuple[MultisetExpression[T], ...]'
    ) -> 'MultisetExpression[T]':
        return type(self)(*new_children, constant=self._constant)

    def _transform_next(
            self, new_children: 'tuple[MultisetExpression[T], ...]',
            outcome: T,
            counts: 'tuple[int, ...]') -> 'tuple[MultisetExpression[T], int]':
        count = self.operator(counts[0])
        return type(self)(*new_children, constant=self._constant), count

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    @property
    def _local_hash_key(self) -> Hashable:
        return type(self), self._constant


class MultisetMultiplyCounts(MultisetCountOperator):
    """Multiplies all counts by the constant."""

    def operator(self, count: int) -> int:
        return count * self._constant

    def __str__(self) -> str:
        return f'({self._children[0]} * {self._constant})'


class MultisetFloordivCounts(MultisetCountOperator):
    """Divides all counts by the constant, rounding down."""

    def operator(self, count: int) -> int:
        return count // self._constant

    def __str__(self) -> str:
        return f'({self._children[0]} // {self._constant})'


class MultisetModuloCounts(MultisetCountOperator):
    """Modulo all counts by the constant."""

    def operator(self, count: int) -> int:
        return count % self._constant

    def __str__(self) -> str:
        return f'({self._children[0]} % {self._constant})'


class MultisetUnique(MultisetCountOperator):
    """Limits the count produced by each outcome."""

    def operator(self, count: int) -> int:
        return min(count, self._constant)

    def __str__(self) -> str:
        if self._constant == 1:
            return f'{self._children[0]}.unique()'
        else:
            return f'{self._children[0]}.unique({self._constant})'


class MultisetKeepCounts(MultisetOperator[T]):

    def __init__(self, child: MultisetExpression[T], /, *,
                 comparison: Literal['==', '!=', '<=', '<', '>=',
                                     '>'], constant: int):
        self._children = (child, )
        self._constant = constant
        operators = {
            '==': operator.eq,
            '!=': operator.ne,
            '<=': operator.le,
            '<': operator.lt,
            '>=': operator.ge,
            '>': operator.gt,
        }
        if comparison not in operators:
            raise ValueError(f'Invalid comparison {comparison}')
        self._comparison = comparison
        self._op = operators[comparison]

    def _copy(
        self, new_children: 'tuple[MultisetExpression[T], ...]'
    ) -> 'MultisetExpression[T]':
        return MultisetKeepCounts(*new_children,
                                  comparison=self._comparison,
                                  constant=self._constant)

    def _transform_next(
            self, new_children: 'tuple[MultisetExpression[T], ...]',
            outcome: T,
            counts: 'tuple[int, ...]') -> 'tuple[MultisetExpression[T], int]':
        if self._op(counts[0], self._constant):
            count = counts[0]
        else:
            count = 0
        return MultisetKeepCounts(*new_children,
                                  comparison=self._comparison,
                                  constant=self._constant), count

    def local_order_preference(self) -> tuple[Order, OrderReason]:
        return Order.Any, OrderReason.NoPreference

    @property
    def _local_hash_key(self) -> Hashable:
        return MultisetKeepCounts, self._comparison, self._constant

    def __str__(self) -> str:
        return f"{self._children[0]}.keep_counts('{self._comparison}', {self._constant})"
