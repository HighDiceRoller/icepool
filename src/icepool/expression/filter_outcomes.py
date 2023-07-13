__docformat__ = 'google'

from functools import cached_property
import icepool

from icepool.expression.multiset_expression import MultisetExpression

from icepool.typing import Order, Outcome, T_contra
from typing import Callable, Collection, Hashable


class FilterOutcomesExpression(MultisetExpression[T_contra]):
    """Keeps all elements in the target set of outcomes, dropping the rest, or vice versa.

    This is similar to `intersection` or `difference`, except the target set is
    considered to have unlimited multiplicity.

    This version has a fixed target and allows functions.
    """

    def __init__(self,
                 inner: MultisetExpression[T_contra],
                 target: Callable[[T_contra], bool] | Collection[T_contra],
                 *,
                 invert: bool = False) -> None:
        """Constructor.

        Args:
            inner: The inner expression.
            target: A callable returning `True` iff the outcome should be kept,
                or a collection of outcomes to keep.
            invert: If set, the filter is inverted.
        """

        self._inner = inner
        self._invert = invert
        if callable(target):
            self._func = target
        else:
            target_set = frozenset(target)

            def function(outcome: T_contra) -> bool:
                return outcome in target_set

            self._func = function

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:
        state, count = self._inner._next_state(state, outcome, *counts)
        if bool(self._func(outcome)) != self._invert:
            return state, count
        else:
            return state, 0

    def _order(self) -> Order:
        return self._inner._order()

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._inner._bound_generators()

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_inner, prefix_start = self._inner._unbind(
            prefix_start, free_start)
        unbound_expression = FilterOutcomesExpression(unbound_inner,
                                                      self._func,
                                                      invert=self._invert)
        unbound_expression._inner = unbound_inner
        return unbound_expression, prefix_start

    def _free_arity(self) -> int:
        return self._inner._free_arity()

    def __str__(self) -> str:
        if self._invert:
            return f'{self._inner}.drop_outcomes(...)'
        else:
            return f'{self._inner}.keep_outcomes(...)'


class FilterOutcomesBinaryExpression(MultisetExpression[T_contra]):
    """Keeps all elements in the target set of outcomes, dropping the rest, or vice versa.

    This is similar to `intersection` or `difference`, except the target set is
    considered to have unlimited multiplicity.

    This version has a variable target.
    """

    def __init__(self,
                 inner: MultisetExpression[T_contra],
                 target: MultisetExpression[T_contra],
                 *,
                 invert: bool = False) -> None:
        """Constructor.

        Args:
            inner: The inner expression.
            target: An expression of outcomes to keep if they have positive count.
            invert: If set, the filter is inverted.
        """
        self._validate_output_arity(inner)
        self._validate_output_arity(target)
        self._inner = inner
        self._target = target
        self._invert = invert

    def _next_state(self, state, outcome: T_contra, *counts:
                    int) -> tuple[Hashable, int]:

        inner_state, target_state = state or (None, None)
        inner_state, inner_count = self._inner._next_state(
            inner_state, outcome, *counts)
        target_state, target_count = self._target._next_state(
            target_state, outcome, *counts)

        if (target_count > 0) != self._invert:
            return (inner_state, target_state), inner_count
        else:
            return (inner_state, target_state), 0

    def _order(self) -> Order:
        return Order.merge(self._inner._order(), self._target._order())

    @cached_property
    def _cached_arity(self) -> int:
        return max(self._inner._free_arity(), self._target._free_arity())

    def _free_arity(self) -> int:
        return self._cached_arity

    @cached_property
    def _cached_bound_generators(
            self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._inner._bound_generators() + self._target._bound_generators(
        )

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._cached_bound_generators

    def _unbind(self, prefix_start: int,
                free_start: int) -> 'tuple[MultisetExpression, int]':
        unbound_inner, prefix_start = self._inner._unbind(
            prefix_start, free_start)
        unbound_target, prefix_start = self._target._unbind(
            prefix_start, free_start)
        unbound_expression = type(self)(unbound_inner,
                                        unbound_target,
                                        invert=self._invert)
        return unbound_expression, prefix_start

    def __str__(self) -> str:
        if self._invert:
            return f'{self._inner}.drop_outcomes({self._target})'
        else:
            return f'{self._inner}.keep_outcomes({self._target})'
