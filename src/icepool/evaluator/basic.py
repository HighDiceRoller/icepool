"""Basic evaluators."""

__docformat__ = 'google'

from icepool.elementwise import binary_elementwise
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.typing import Outcome, Order

import operator

from typing import Any, Callable, Final, Literal, Mapping


class ExpandEvaluator(MultisetEvaluator[Any, tuple]):
    """Expands all results of a generator.

    This is expensive and not recommended unless there are few possibilities.

    Outcomes with negative count will be treated as 0 count.
    """

    def next_state(self, state, outcome, count):
        """Implementation."""
        return (state or ()) + (outcome,) * count

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any

    def final_outcome(self, final_state) -> tuple:
        """Implementation."""
        if final_state is None:
            return ()
        return tuple(sorted(final_state))


class SumEvaluator(MultisetEvaluator[Any, Any]):
    """Sums all outcomes."""

    def __init__(self, map: Callable | Mapping | None = None) -> None:
        """Constructor.

        map: If provided, outcomes will be mapped according to this just
            before summing.
        """
        if map is None:

            def map_func(outcome):
                return outcome

            self._map = map_func
        elif callable(map):
            self._map = map
        else:
            map_dict = {k: v for k, v in map.items()}

            def map_func(outcome):
                return map_dict[outcome]

            self._map = map_func

    def next_state(self, state, outcome, count):
        """Implementation."""
        outcome = self._map(outcome)
        if state is None:
            if count == 1:
                # The outcome does not need to support addition or
                # multiplication in this case.
                return outcome
            return binary_elementwise(outcome, count, operator.mul)
        else:
            contribution = binary_elementwise(outcome, count, operator.mul)
            return binary_elementwise(state, contribution, operator.add)

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any


sum_evaluator: Final = SumEvaluator()
"""Shared instance for caching."""


class CountEvaluator(MultisetEvaluator[Any, int]):
    """Returns the total count of outcomes.

    Usually not very interesting unless the counts are adjusted by
    `AdjustIntCountEvaluator`.
    """

    def next_state(self, state, outcome, count):
        """Implementation."""
        return (state or 0) + count

    def final_outcome(self, final_state) -> int:
        """Implementation."""
        return final_state or 0

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any


count_evaluator: Final = CountEvaluator()
"""Shared instance for caching."""


class AnyEvaluator(MultisetEvaluator[Any, bool]):
    """Returns `True` iff at least one count is positive."""

    def next_state(self, state, outcome, count):
        """Implementation."""
        return state or (count > 0)

    def final_outcome(self, final_state) -> bool:
        """Implementation."""
        return final_state or False

    def order(self) -> Literal[Order.Any]:
        """Allows any order."""
        return Order.Any


any_evaluator: Final = AnyEvaluator()
"""Shared instance for caching."""
