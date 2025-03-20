__docformat__ = 'google'

import icepool
from icepool.collection.counts import Counts
from icepool.order import Order, OrderReason, merge_order_preferences
from icepool.population.keep import highest_slice, lowest_slice

import bisect
from functools import cached_property
import itertools
import operator
import random

from icepool.typing import Q, T, U, ImplicitConversionError, T
from types import EllipsisType
from typing import (TYPE_CHECKING, Any, Callable, Collection, Generic,
                    Hashable, Iterable, Iterator, Literal, Mapping,
                    MutableSequence, Sequence, Type, TypeAlias, TypeVar, cast,
                    overload)

from abc import ABC, abstractmethod


class MultisetExpressionBase(ABC, Generic[T, Q]):
    _children: 'tuple[MultisetExpressionBase[T, Any], ...]'
    """A tuple of child expressions. These are assumed to the positional arguments of the constructor."""

    @abstractmethod
    def _prepare(
        self
    ) -> Iterator[tuple['Sequence[MultisetDungeonlet[T, Any]]',
                        'Sequence[MultisetQuestlet[T]]',
                        'Sequence[MultisetSource[T, Any]]', int]]:
        """Prepare for evaluation.

        Yields:
            * A flattened tuple of dungeonlets.
            * A flattened tuple of questlets of the same length.
            * A tuple of freed sources.
            * The weight of this result.
        """


class MultisetDungeonlet(ABC, Generic[T, Q], Hashable):
    child_indexes: 'tuple[int, ...]'
    """The relative (therefore negative) indexes of this node's children."""

    @abstractmethod
    def next_state(self, state: Hashable, order: Order, outcome: T,
                   child_counts: MutableSequence, free_counts: Iterator,
                   param_counts: Sequence) -> tuple[Hashable, int]:
        """Advances the state of this dungeonlet.
        
        Args:
            state: The local state.
            order: The order in which outcomes are seen by this method.
            outcome: The current outcome.
            child_counts: The counts of the child nodes.
            free_counts: The counts produced by freed sources.
                This is an iterator which will be progressively consumed by
                free variables.
            param_counts: The counts produced by params.

        Returns:
            The next local state and the count produced by this node.

        Raises:
            UnsupportedOrderError if the order is not supported.
        """

    @property
    @abstractmethod
    def hash_key(self):
        """A hash key for this node. This should include child_indexes."""

    def __eq__(self, other):
        if not isinstance(other, MultisetDungeonlet):
            return False
        return self.hash_key == other.hash_key

    def __hash__(self):
        return hash(self.hash_key)


class MultisetFreeVariable(MultisetDungeonlet[T, Q]):
    """A dungeonlet representing a source that has been freed."""
    child_indexes = ()

    def next_state(self, state, order, outcome, child_counts, free_counts,
                   param_counts):
        return None, next(free_counts)


class MultisetSource(Generic[T, Q], Hashable):

    @abstractmethod
    def outcomes(self) -> Sequence[T]:
        """The possible outcomes that could be generated, in ascending order."""

    @abstractmethod
    def pop(self, order: Order,
            outcome: T) -> Iterator[tuple['MultisetSource', Q, int]]:
        """
        Args:
            order: The order in which the pop occurs.
            outcome: The outcome to pop.
        
        Yields:
            * This source with the outcome popped.
            * The count of that outcome.
            * The weight for this many of the outcome appearing.

            If the argument does not match the outcome for the given order,
            the result is:

            * `self`
            * Zero count.
            * weight = 1.
        """

    @abstractmethod
    def order_preference(self) -> tuple[Order, OrderReason]:
        """The preferred order of this source and a reason why the order is preferred."""

    def min_outcome(self) -> T:
        return self.outcomes()[0]

    def max_outcome(self) -> T:
        return self.outcomes()[-1]


class MultisetQuestlet(Generic[T]):

    def initial_state(self, order: Order, outcomes: Sequence[T], /,
                      **kwargs) -> Hashable:
        """Optional: the initial state of this node.
        TODO: Should this get cardinalities?

        Args:
            order: The order in which `next_state` will see outcomes.
            outcomes: All outcomes that will be seen by `next_state` in ascending order.
            kwargs: Any keyword arguments that were passed to `evaluate()`.

        Raises:
            UnsupportedOrderError if the given order is not supported.
        """
        return None
