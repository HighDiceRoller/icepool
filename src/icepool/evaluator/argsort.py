__docformat__ = 'google'

from icepool.evaluator.multiset_evaluator import MultisetEvaluator

from icepool.order import Order, UnsupportedOrder
from typing import Any, Literal


class ArgsortEvaluatorDrop(MultisetEvaluator[Any, tuple[int, ...]]):
    """Returns the indexes of the originating multisets for each rank in their additive union.
    
    In this version, if the same outcome appears in more than one multiset,
    one element of that outcome is dropped from each multiset. This is repeated
    until only one multiset has elements of that outcome.
    """

    def __init__(self,
                 *,
                 order: Order = Order.Descending,
                 limit: int | None = None):
        self._order = order
        self._limit = limit

    def initial_state(self, order, outcomes, *sizes):
        if order != self._order:
            raise UnsupportedOrder(
                'argsort must be evaluated in the given order.')
        return ()

    def next_state(self, state, order, outcome, *counts):
        """Implementation."""
        if self._limit is None or len(state) < self._limit:
            max_count = 0
            tie_count = 0
            max_index = None
            for index, count in enumerate(counts):
                if count > max_count:
                    tie_count = max_count
                    max_count = count
                    max_index = index
                elif count > tie_count:
                    tie_count = count
            append_count = max_count - tie_count if self._limit is None else min(
                max_count - tie_count, self._limit - len(state))
            if append_count > 0:
                return state + (max_index, ) * append_count
        return state

    def order(self):
        return self._order

    @property
    def next_state_key(self):
        return (type(self), self._order, self._limit)


class ArgsortEvaluatorLeft(MultisetEvaluator[Any, tuple[int, ...]]):
    """Returns the indexes of the originating multisets for each rank in their additive union.
    
    In this version, if the same outcome appears in more than one multiset,
    the elements coming from the leftmost multiset (lower indexes) are ranked
    earlier.
    """

    def __init__(self,
                 *,
                 order: Order = Order.Descending,
                 limit: int | None = None):
        self._order = order
        self._limit = limit

    def initial_state(self, order, outcomes, *sizes):
        if order != self._order:
            raise UnsupportedOrder(
                'argsort must be evaluated in the given order.')
        return ()

    def next_state(self, state, order, outcome, *counts):
        """Implementation."""
        if state is None:
            state = ()
        for index, count in enumerate(counts):
            append_count = count if self._limit is None else min(
                count, self._limit - len(state))
            if append_count > 0:
                state += (index, ) * append_count
                if len(state) == self._limit:
                    return state
        return state

    @property
    def next_state_key(self):
        return (type(self), self._order, self._limit)


class ArgsortEvaluatorRight(MultisetEvaluator[Any, tuple[int, ...]]):
    """Returns the indexes of the originating multisets for each rank in their additive union.
    
    In this version, if the same outcome appears in more than one multiset,
    the elements coming from the rightmost multiset (higher indexes) are ranked
    earlier.
    """

    def __init__(self,
                 *,
                 order: Order = Order.Descending,
                 limit: int | None = None):
        self._order = order
        self._limit = limit

    def initial_state(self, order, outcomes, *sizes):
        if order != self._order:
            raise UnsupportedOrder(
                'argsort must be evaluated in the given order.')
        return ()

    def next_state(self, state, order, outcome, *counts):
        """Implementation."""
        if state is None:
            state = ()
        for index, count in reversed(list(enumerate(counts))):
            append_count = count if self._limit is None else min(
                count, self._limit - len(state))
            if append_count > 0:
                state += (index, ) * append_count
                if len(state) == self._limit:
                    return state
        return state

    @property
    def next_state_key(self):
        return (type(self), self._order, self._limit)


class ArgsortGroupedEvaluator(MultisetEvaluator[Any, tuple[tuple[int, ...],
                                                           ...]]):
    """Returns the indexes of the originating multisets for each rank in their additive union.
    
    This version groups all ties together, returning a tuple for each rank
    rather than a single `int`.
    """

    def __init__(self,
                 *,
                 order: Order = Order.Descending,
                 limit: int | None = None):
        self._order = order
        self._limit = limit

    def initial_state(self, order, outcomes, *sizes):
        if order != self._order:
            raise UnsupportedOrder(
                'argsort_grouped must be evaluated in the given order.')
        return ()

    def next_state(self, state, order, outcome, *counts):
        """Implementation."""
        if (self._limit is None or len(state) < self._limit) and any(
                count > 0 for count in counts):
            to_append = sum(((i, ) * count for i, count in enumerate(counts)),
                            start=())
            state += (to_append, )
        return state

    @property
    def next_state_key(self):
        return (type(self), self._order, self._limit)
