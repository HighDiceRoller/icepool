__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

import inspect
import operator
from abc import abstractmethod
from functools import cached_property, reduce

from icepool.typing import Order, Outcome, T_contra
from typing import Callable, Hashable, Sequence, cast, overload


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

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:

        inner_states = state or (None, ) * len(self._inners)
        inner_states, inner_counts = zip(
            *(inner._next_state(inner_state, outcome, *counts)
              for inner, inner_state in zip(self._inners, inner_states)))

        count = self._function(outcome, *inner_counts)
        return state, count

    def _order(self) -> Order:
        return Order.merge(*(inner._order() for inner in self._inners))

    @cached_property
    def _cached_arity(self) -> int:
        return max(inner._free_arity() for inner in self._inners)

    def _free_arity(self) -> int:
        return self._cached_arity

    @cached_property
    def _cached_bound_generators(
            self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return reduce(operator.add,
                      (inner._bound_generators() for inner in self._inners))

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._cached_bound_generators

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_inners = []
        for inner in self._inners:
            unbound_inner, prefix_start = inner._unbind(
                prefix_start, free_start)
            unbound_inners.append(unbound_inner)
        unbound_expression = type(self)(*unbound_inners,
                                        function=self._function)
        return unbound_expression, prefix_start


class AdjustCountsExpression(MultisetExpression[T_contra]):

    def __init__(self, inner: MultisetExpression[T_contra],
                 constant: int) -> None:
        self._validate_output_arity(inner)
        self._inner = inner
        self._constant = constant

    @abstractmethod
    def adjust_count(self, count: int, constant: int) -> int:
        """Adjusts the count."""

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:
        state, count = self._inner._next_state(state, outcome, *counts)
        count = self.adjust_count(count, self._constant)
        return state, count

    def _order(self) -> Order:
        return self._inner._order()

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._inner._bound_generators()

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_inner, prefix_start = self._inner._unbind(
            prefix_start, free_start)
        unbound_expression = type(self)(unbound_inner, self._constant)
        return unbound_expression, prefix_start

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

    def __init__(self, inner: MultisetExpression[T_contra], constant: int,
                 op: Callable[[int, int], bool]):
        super().__init__(inner, constant)
        self._op = op

    def adjust_count(self, count: int, constant: int) -> int:
        if self._op(count, constant):
            return count
        else:
            return 0

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_inner, prefix_start = self._inner._unbind(
            prefix_start, free_start)
        unbound_expression = type(self)(unbound_inner, self._constant,
                                        self._op)
        return unbound_expression, prefix_start

    def __str__(self) -> str:
        return f'{self._inner}.keep_counts_{self._op.__name__}({self._constant})'


class UniqueExpression(AdjustCountsExpression):
    """Limits the count produced by each outcome."""

    def adjust_count(self, count: int, constant: int) -> int:
        return min(count, constant)

    def __str__(self) -> str:
        if self._constant == 1:
            return f'{self._inner}.unique()'
        else:
            return f'{self._inner}.unique({self._constant})'
