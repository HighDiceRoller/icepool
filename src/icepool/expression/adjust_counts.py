__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

import inspect
import operator
from abc import abstractmethod
from functools import cached_property, reduce

from icepool.typing import Order, Outcome, T
from typing import Callable, Hashable, Literal, Sequence, cast, overload


class MapCountsExpression(MultisetExpression[T]):
    """Expression that maps outcomes and counts to new counts."""

    _function: Callable[..., int]

    def __init__(self, *children: MultisetExpression[T],
                 function: Callable[..., int]) -> None:
        """Constructor.

        Args:
            children: The children expression(s).
            function: A function that takes `outcome, *counts` and produces a
                combined count.
        """
        for child in children:
            self._validate_output_arity(child)
        self._children = children
        self._function = function

    def _make_unbound(self, *unbound_children) -> 'icepool.MultisetExpression':
        return MapCountsExpression(*unbound_children, function=self._function)

    def _next_state(self, state, outcome: T, *counts:
                    int) -> tuple[Hashable, int]:

        child_states = state or (None, ) * len(self._children)
        child_states, child_counts = zip(
            *(child._next_state(child_state, outcome, *counts)
              for child, child_state in zip(self._children, child_states)))

        count = self._function(outcome, *child_counts)
        return state, count

    def order(self) -> Order:
        return Order.merge(*(child.order() for child in self._children))

    @cached_property
    def _cached_arity(self) -> int:
        return max(child._free_arity() for child in self._children)

    def _free_arity(self) -> int:
        return self._cached_arity


class AdjustCountsExpression(MultisetExpression[T]):

    def __init__(self, child: MultisetExpression[T], /, *,
                 constant: int) -> None:
        self._validate_output_arity(child)
        self._children = (child, )
        self._constant = constant

    def _make_unbound(self, *unbound_children) -> 'icepool.MultisetExpression':
        return type(self)(*unbound_children, constant=self._constant)

    @abstractmethod
    def adjust_count(self, count: int, constant: int) -> int:
        """Adjusts the count."""

    def _next_state(self, state, outcome: T, *counts:
                    int) -> tuple[Hashable, int]:
        state, count = self._children[0]._next_state(state, outcome, *counts)
        count = self.adjust_count(count, self._constant)
        return state, count

    def order(self) -> Order:
        return self._children[0].order()

    def _free_arity(self) -> int:
        return self._children[0]._free_arity()


class MultiplyCountsExpression(AdjustCountsExpression):
    """Multiplies all counts by the constant."""

    def adjust_count(self, count: int, constant: int) -> int:
        return count * constant

    def __str__(self) -> str:
        return f'({self._children[0]} * {self._constant})'


class FloorDivCountsExpression(AdjustCountsExpression):
    """Divides all counts by the constant, rounding down."""

    def adjust_count(self, count: int, constant: int) -> int:
        return count // constant

    def __str__(self) -> str:
        return f'({self._children[0]} // {self._constant})'


class ModuloCountsExpression(AdjustCountsExpression):
    """Modulo all counts by the constant."""

    def adjust_count(self, count: int, constant: int) -> int:
        return count % constant

    def __str__(self) -> str:
        return f'({self._children[0]} % {self._constant})'


class KeepCountsExpression(AdjustCountsExpression):

    def __init__(self, child: MultisetExpression[T], /, *,
                 comparison: Literal['==', '!=', '<=', '<', '>=',
                                     '>'], constant: int):
        super().__init__(child, constant=constant)
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

    def _make_unbound(self, *unbound_children) -> 'icepool.MultisetExpression':
        return KeepCountsExpression(*unbound_children,
                                    comparison=self._comparison,
                                    constant=self._constant)

    def adjust_count(self, count: int, constant: int) -> int:
        if self._op(count, constant):
            return count
        else:
            return 0

    def __str__(self) -> str:
        return f"{self._children[0]}.keep_counts('{self._comparison}', {self._constant})"


class UniqueExpression(AdjustCountsExpression):
    """Limits the count produced by each outcome."""

    def adjust_count(self, count: int, constant: int) -> int:
        return min(count, constant)

    def __str__(self) -> str:
        if self._constant == 1:
            return f'{self._children[0]}.unique()'
        else:
            return f'{self._children[0]}.unique({self._constant})'
