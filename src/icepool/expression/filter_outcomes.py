__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

from icepool.typing import Order, Outcome, T_contra
from typing import Callable, Collection, Hashable


class FilterOutcomesExpression(MultisetExpression[T_contra]):
    """Keeps all elements in the target set of outcomes, dropping the rest, or vice versa.

    This is similar to `intersection` or `difference`, except the target set is
    considered to have unlimited multiplicity.
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

            def func(outcome: T_contra) -> bool:
                return outcome in target_set

            self._func = func

    def _next_state(self, state, outcome: T_contra,
                    *counts: int) -> tuple[Hashable, int]:
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
        return f'{self._inner}.filter_outcomes()'
