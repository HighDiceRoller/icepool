__docformat__ = 'google'

from icepool.expression.multiset_expression import MultisetExpression
from icepool.operator.multiset_operator import MultisetOperator

from typing import Callable, Collection
from icepool.typing import T


class MultisetFilterOutcomes(MultisetOperator[T]):
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

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    param_counts):
        if bool(self._func(outcome)) != self._invert:
            count = child_counts[0]
        else:
            count = 0
        return None, count

    @property
    def _expression_key(self):
        return type(self), self._func, self._invert

    def __str__(self) -> str:
        if self._invert:
            return f'{self._children[0]}.drop_outcomes(...)'
        else:
            return f'{self._children[0]}.keep_outcomes(...)'


class MultisetFilterOutcomesBinary(MultisetOperator[T]):
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
        self._source = source
        self._target = target
        self._children = (source, target)
        self._invert = invert

    def _next_state(self, state, order, outcome, child_counts, source_counts,
                    param_counts):
        source_count, target_count = child_counts
        if (target_count > 0) != self._invert:
            count = source_count
        else:
            count = 0
        return None, count

    @property
    def _expression_key(self):
        return type(self), self._invert

    def __str__(self) -> str:
        if self._invert:
            return f'{self._source}.drop_outcomes({self._target})'
        else:
            return f'{self._source}.keep_outcomes({self._target})'
