__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

import inspect
from abc import abstractmethod
from functools import cached_property

from icepool.typing import Order, Outcome, T_contra
from typing import Callable, Hashable, Sequence, cast, overload


class MapCountsExpression(MultisetExpression[T_contra]):
    """Expression that maps outcomes and counts to new counts."""

    _func: Callable[[T_contra, int], int]

    @overload
    def __init__(self, inner: MultisetExpression[T_contra],
                 func: Callable[[int], int]) -> None:
        ...

    @overload
    def __init__(self, inner: MultisetExpression[T_contra],
                 func: Callable[[T_contra, int], int]) -> None:
        ...

    def __init__(
            self, inner: MultisetExpression[T_contra],
            func: Callable[[int], int] | Callable[[T_contra, int], int]
    ) -> None:
        """Constructor.

        Args:
            inner: The inner expression.
            func: A function that takes either `count` or `outcome, count` and
                produces a modified count.
        """
        self._validate_output_arity(inner)
        self._inner = inner

        parameters = inspect.signature(func, follow_wrapped=False).parameters
        if len(parameters.values()) == 1:
            count_only_func = cast(Callable[[int], int], func)

            def wrapped(outcome: T_contra, count: int) -> int:
                return count_only_func(count)

            self._func = wrapped

        else:
            func = cast(Callable[[T_contra, int], int], func)
            self._func = func

    def _next_state(self, state, outcome: T_contra,
                    *counts: int) -> tuple[Hashable, int]:
        state, count = self._inner._next_state(state, outcome, *counts)
        count = self._func(outcome, count)
        return state, count

    def _order(self) -> Order:
        return self._inner._order()

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._inner._bound_generators()

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_inner, prefix_start = self._inner._unbind(
            prefix_start, free_start)
        unbound_expression = MapCountsExpression(unbound_inner, self._func)
        return unbound_expression, prefix_start

    def _free_arity(self) -> int:
        return self._inner._free_arity()


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

    def _next_state(self, state, outcome: T_contra,
                    *counts: int) -> tuple[Hashable, int]:
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
