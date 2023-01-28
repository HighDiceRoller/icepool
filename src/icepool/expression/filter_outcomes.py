__docformat__ = 'google'

import icepool

from icepool.expression.multiset_expression import MultisetExpression

from icepool.typing import Order, Outcome, T_contra
from typing import Callable, Collection, Hashable


class FilterOutcomesExpression(MultisetExpression[T_contra]):
    """Drops all elements not in the target set of outcomes.

    This is similar to `intersection`, except the target set is considered to
    have unlimited multiplicity.
    """

    def __init__(
            self, inner: MultisetExpression[T_contra],
            target: Callable[[T_contra], bool] | Collection[T_contra]) -> None:
        """Constructor.

        Args:
            inner: The inner expression.
            target: A collection of outcomes to keep, or a callable returning
                `True` iff the outcome should be kept.
        """

        self._inner = inner
        if callable(target):
            self._func = target
        else:
            target_set = frozenset(target)

            def func(outcome: T_contra) -> bool:
                return outcome in target_set

            self._func = func

    def _next_state(self, state, outcome: T_contra, bound_counts: tuple[int,
                                                                        ...],
                    counts: tuple[int, ...]) -> tuple[Hashable, int]:
        state, count = self._inner._next_state(state, outcome, bound_counts,
                                               counts)
        if self._func(outcome):
            return state, count
        else:
            return state, 0

    def _order(self) -> Order:
        return self._inner._order()

    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return self._inner._bound_generators()

    def _arity(self) -> int:
        return self._inner._arity()