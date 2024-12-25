__docformat__ = 'google'

from functools import cached_property
import icepool

from icepool.expression.multiset_expression import MultisetExpression

from icepool.typing import Order, Outcome, T
from typing import Callable, Collection, Hashable


class FilterOutcomesExpression(MultisetExpression[T]):
    """Keeps all elements in the target set of outcomes, dropping the rest, or vice versa.

    This is similar to `intersection` or `difference`, except the target set is
    considered to have unlimited multiplicity.

    This version has a fixed target and allows functions.
    """

    def __init__(self,
                 child: MultisetExpression[T],
                 /,
                 *,
                 target: Callable[[T], bool] | Collection[T],
                 invert: bool = False) -> None:
        """Constructor.

        Args:
            child: The child expression.
            target: A callable returning `True` iff the outcome should be kept,
                or a collection of outcomes to keep.
            invert: If set, the filter is inverted.
        """

        self._children = (child, )
        self._invert = invert
        if callable(target):
            self._func = target
        else:
            target_set = frozenset(target)

            def function(outcome: T) -> bool:
                return outcome in target_set

            self._func = function

    def _make_unbound(self, *unbound_children) -> 'icepool.MultisetExpression':
        return FilterOutcomesExpression(*unbound_children,
                                        invert=self._invert,
                                        target=self._func)

    def _next_state(self, state, outcome: T, *counts:
                    int) -> tuple[Hashable, int]:
        state, count = self._children[0]._next_state(state, outcome, *counts)
        if bool(self._func(outcome)) != self._invert:
            return state, count
        else:
            return state, 0

    def order(self) -> Order:
        return self._children[0].order()

    def _free_arity(self) -> int:
        return self._children[0]._free_arity()

    def __str__(self) -> str:
        if self._invert:
            return f'{self._children[0]}.drop_outcomes(...)'
        else:
            return f'{self._children[0]}.keep_outcomes(...)'


class FilterOutcomesBinaryExpression(MultisetExpression[T]):
    """Keeps all elements in the target set of outcomes, dropping the rest, or vice versa.

    This is similar to `intersection` or `difference`, except the target set is
    considered to have unlimited multiplicity.

    This version has a variable target.
    """

    def __init__(self,
                 source: MultisetExpression[T],
                 target: MultisetExpression[T],
                 *,
                 invert: bool = False) -> None:
        """Constructor.

        Args:
            child: The child expression.
            target: An expression of outcomes to keep if they have positive count.
            invert: If set, the filter is inverted.
        """
        self._validate_output_arity(source)
        self._validate_output_arity(target)
        self._source = source
        self._target = target
        self._children = (source, target)
        self._invert = invert

    def _make_unbound(self, *unbound_children) -> 'icepool.MultisetExpression':
        return FilterOutcomesBinaryExpression(*unbound_children,
                                              invert=self._invert)

    def _next_state(self, state, outcome: T, *counts:
                    int) -> tuple[Hashable, int]:

        source_state, target_state = state or (None, None)
        source_state, source_count = self._source._next_state(
            source_state, outcome, *counts)
        target_state, target_count = self._target._next_state(
            target_state, outcome, *counts)

        if (target_count > 0) != self._invert:
            return (source_state, target_state), source_count
        else:
            return (source_state, target_state), 0

    def order(self) -> Order:
        return Order.merge(self._source.order(), self._target.order())

    @cached_property
    def _cached_arity(self) -> int:
        return max(self._source._free_arity(), self._target._free_arity())

    def _free_arity(self) -> int:
        return self._cached_arity

    def __str__(self) -> str:
        if self._invert:
            return f'{self._source}.drop_outcomes({self._target})'
        else:
            return f'{self._source}.keep_outcomes({self._target})'
