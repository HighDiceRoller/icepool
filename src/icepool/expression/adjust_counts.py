__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

import inspect
import operator
from abc import abstractmethod
from functools import cached_property, reduce

from icepool.typing import Order, Outcome, T_contra
from typing import Callable, Hashable, Literal, Sequence, cast, overload


class MapCountsExpression(MultisetExpression[T_contra]):
    """Expression that maps outcomes and counts to new counts."""

    _function: Callable[..., int]

    def __init__(self, *inners: MultisetExpression[T_contra],
                 function: Callable[..., int]) -> None:
        """Constructor.

        Args:
            inner: The inner expression.
            function: A function that takes `outcome, *counts` and produces a
                combined count.
        """
        for inner in inners:
            self._validate_output_arity(inner)
        self._inners = inners
        self._function = function

    def _make_unbound(self, *unbound_inners) -> 'icepool.MultisetExpression':
        return MapCountsExpression(*unbound_inners, function=self._function)

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:

        inner_states = state or (None, ) * len(self._inners)
        inner_states, inner_counts = zip(
            *(inner._next_state(inner_state, outcome, *counts)
              for inner, inner_state in zip(self._inners, inner_states)))

        count = self._function(outcome, *inner_counts)
        return state, count

    def order(self) -> Order:
        return Order.merge(*(inner.order() for inner in self._inners))

    @cached_property
    def _cached_arity(self) -> int:
        return max(inner._free_arity() for inner in self._inners)

    def _free_arity(self) -> int:
        return self._cached_arity


class AdjustCountsExpression(MultisetExpression[T_contra]):

    def __init__(self, inner: MultisetExpression[T_contra], /, *,
                 constant: int) -> None:
        self._validate_output_arity(inner)
        self._inner = inner
        self._inners = (inner, )
        self._constant = constant

    def _make_unbound(self, *unbound_inners) -> 'icepool.MultisetExpression':
        return type(self)(*unbound_inners, constant=self._constant)

    @abstractmethod
    def adjust_count(self, count: int, constant: int) -> int:
        """Adjusts the count."""

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:
        state, count = self._inner._next_state(state, outcome, *counts)
        count = self.adjust_count(count, self._constant)
        return state, count

    def order(self) -> Order:
        return self._inner.order()

    def _free_arity(self) -> int:
        return self._inner._free_arity()


class MultiplyCountsExpression(AdjustCountsExpression):
    """Multiplies all counts by the constant."""

    def adjust_count(self, count: int, constant: int) -> int:
        return count * constant

    def __str__(self) -> str:
        return f'({self._inner} * {self._constant})'


class FloorDivCountsExpression(AdjustCountsExpression):
    """Divides all counts by the constant, rounding down."""

    def adjust_count(self, count: int, constant: int) -> int:
        return count // constant

    def __str__(self) -> str:
        return f'({self._inner} // {self._constant})'


class ModuloCountsExpression(AdjustCountsExpression):
    """Modulo all counts by the constant."""

    def adjust_count(self, count: int, constant: int) -> int:
        return count % constant

    def __str__(self) -> str:
        return f'({self._inner} % {self._constant})'


class KeepCountsExpression(AdjustCountsExpression):

    def __init__(self, inner: MultisetExpression[T_contra], /, *,
                 comparison: Literal['==', '!=', '<=', '<', '>=',
                                     '>'], constant: int):
        super().__init__(inner, constant=constant)
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

    def _make_unbound(self, *unbound_inners) -> 'icepool.MultisetExpression':
        return KeepCountsExpression(*unbound_inners,
                                    comparison=self._comparison,
                                    constant=self._constant)

    def adjust_count(self, count: int, constant: int) -> int:
        if self._op(count, constant):
            return count
        else:
            return 0

    def __str__(self) -> str:
        return f"{self._inner}.keep_counts('{self._comparison}', {self._constant})"


class UniqueExpression(AdjustCountsExpression):
    """Limits the count produced by each outcome."""

    def adjust_count(self, count: int, constant: int) -> int:
        return min(count, constant)

    def __str__(self) -> str:
        if self._constant == 1:
            return f'{self._inner}.unique()'
        else:
            return f'{self._inner}.unique({self._constant})'
