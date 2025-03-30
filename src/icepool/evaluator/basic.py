"""Basic evaluators."""

__docformat__ = 'google'

import icepool
from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.order import Order

from typing import Any, Callable, Final, Hashable, Mapping


class ExpandEvaluator(MultisetEvaluator[Any, tuple]):
    """All elements of the multiset.

    This is expensive and not recommended unless there are few possibilities.

    Outcomes with negative count will be treated as 0 count.
    """

    def next_state(self, state, order, outcome, count):
        """Implementation."""
        return (state or ()) + (outcome, ) * count

    def final_outcome(  # type: ignore
            self,
            final_state,
            order_,
            outcomes,
            size,
            order: Order = Order.Ascending) -> tuple:
        """Implementation."""
        if final_state is None:
            return ()
        reverse = order != Order.Ascending
        return tuple(sorted(final_state, reverse=reverse))

    # No dungeon key, as this isn't consider worth persistently hashing.


class SumEvaluator(MultisetEvaluator[Any, Any]):
    """Sums all outcomes."""

    _next_state_key: Hashable

    def __init__(self, map: Callable | Mapping | None = None) -> None:
        """Constructor.

        map: If provided, outcomes will be mapped according to this just
            before summing.
        """
        if map is None:

            def map_func(outcome):
                return outcome

            self._map = map_func
            self._next_state_key = (SumEvaluator, )
        elif callable(map):
            self._map = map
            self._next_state_key = None
        else:
            map_dict = {k: v for k, v in map.items()}

            def map_func(outcome):
                return map_dict[outcome]

            self._map = map_func
            self._next_state_key = None

    def next_state(self, state, order, outcome, count):
        """Implementation."""
        outcome = self._map(outcome)
        if state is None:
            if count == 1:
                # The outcome does not need to support addition or
                # multiplication in this case.
                return outcome
            return outcome * count
        else:
            return state + outcome * count

    @property
    def next_state_key(self):
        return self._next_state_key


sum_evaluator: Final = SumEvaluator()
"""Shared instance for caching."""


class SizeEvaluator(MultisetEvaluator[Any, int]):
    """Returns the total number of elements.

    Usually not very interesting unless the counts are adjusted by
    `unique` etc.
    """

    def next_state(self, state, order, outcome, count):
        """Implementation."""
        return (state or 0) + count

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, size) -> int:
        """Implementation."""
        return final_state or 0

    @property
    def next_state_key(self):
        return (type(self), )


size_evaluator: Final = SizeEvaluator()
"""Shared instance for caching."""


class AnyEvaluator(MultisetEvaluator[Any, bool]):
    """Returns `True` iff at least one count is positive."""

    def next_state(self, state, order, outcome, count):
        """Implementation."""
        return state or (count > 0)

    def final_outcome(  # type: ignore
            self, final_state, order, outcomes, size) -> bool:
        """Implementation."""
        return final_state or False

    @property
    def next_state_key(self):
        return (type(self), )


any_evaluator: Final = AnyEvaluator()
"""Shared instance for caching."""
