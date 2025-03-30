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

from icepool.typing import Q, T, U, MaybeHashKeyed, ImplicitConversionError, T
from types import EllipsisType
from typing import (TYPE_CHECKING, Any, Callable, Collection, Generic,
                    Hashable, Iterable, Iterator, Literal, Mapping,
                    MutableSequence, NamedTuple, Sequence, Type, TypeAlias,
                    TypeVar, cast, overload)

from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from icepool.expression.multiset_param import MultisetParamBase


class MultisetExpressionBase(Generic[T, Q], MaybeHashKeyed):
    """Abstract methods are protected so as to not be distracting."""

    @abstractmethod
    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        """Prepare for evaluation.

        Yields:
            dungeonlet_flat, questlet_flat, sources, weight
        """

    @property
    @abstractmethod
    def _has_param(self) -> bool:
        """Whether this expression tree contains any param."""

    @property
    @abstractmethod
    def _param_type(self) -> 'Type[MultisetParamBase]':
        """The type of param corresponding to the output of this expression."""

    @property
    @abstractmethod
    def _static_keepable(self) -> bool:
        """Whether this expression supports keep operations via static analysis."""


class Dungeonlet(Generic[T, Q], MaybeHashKeyed):
    child_indexes: tuple[int, ...]
    """The relative (therefore negative) indexes of this node's children."""

    @abstractmethod
    def next_state(self, state: Hashable, order: Order, outcome: T,
                   child_counts: MutableSequence, source_counts: Iterator,
                   param_counts: Sequence) -> tuple[Hashable, Q]:
        """Advances the state of this dungeonlet.
        
        Args:
            state: The local state.
            order: The order in which outcomes are seen by this method.
            outcome: The current outcome.
            child_counts: The counts of the child nodes.
            source_counts: The counts produced by sources.
                This is an iterator which will be progressively consumed by
                free variables.
            param_counts: The counts produced by params.

        Returns:
            The next local state and the count produced by this node.

        Raises:
            UnsupportedOrder if the order is not supported.
        """

    def __eq__(self, other):
        if not isinstance(other, Dungeonlet):
            return False
        return self.hash_key == other.hash_key

    def __hash__(self):
        return hash(self.hash_key)


class MultisetFreeVariable(Dungeonlet[T, Q]):
    child_indexes = ()

    def next_state(self, state, order, outcome, child_counts, source_counts,
                   param_counts):
        return None, next(source_counts)

    @property
    def hash_key(self):
        return MultisetFreeVariable


class MultisetSourceBase(Generic[T, Q], MaybeHashKeyed):

    @abstractmethod
    def outcomes(self) -> tuple[T, ...]:
        """The possible outcomes that could be generated, in ascending order."""

    @abstractmethod
    def size(self) -> Q | None:
        """The total number of elements output by this source, if only non-negative counts are output.
        
        If total number of elements is not constant or unknown, or if there are
        negative counts, the result is `None`.
        """

    @abstractmethod
    def pop(self, order: Order,
            outcome: T) -> Iterator[tuple['MultisetSourceBase', Q, int]]:
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

    @abstractmethod
    def is_resolvable(self) -> bool:
        """Whether this source contains any probability."""

    def min_outcome(self) -> T:
        return self.outcomes()[0]

    def max_outcome(self) -> T:
        return self.outcomes()[-1]


class Questlet(Generic[T, Q]):
    child_indexes: tuple[int, ...]
    """The relative (therefore negative) indexes of this node's children."""

    @abstractmethod
    def initial_state(self, order: Order, outcomes: Sequence[T],
                      child_sizes: MutableSequence, source_sizes: Iterator,
                      param_sizes: Sequence) -> tuple[Hashable, Q | None]:
        """Optional: the initial state of this node.

        Args:
            order: The order in which `next_state` will see outcomes.
            outcomes: All outcomes that will be seen by `next_state` in ascending order.
            child_counts: The sizes of the child nodes.
            source_counts: The sizes produced by sources.
                This is an iterator which will be progressively consumed by
                free variables.
            param_counts: The sizes produced by params.

        Returns:
            The initial state, and the size of this node.

        Raises:
            UnsupportedOrder if the given order is not supported.
        """


class DungeonletCallTree(Generic[T], NamedTuple):
    flats: 'tuple[tuple[Dungeonlet[T, Any], ...], ...]'
    calls: 'tuple[DungeonletCallTree, ...]'

    def next_state(
            self, statelet_tree: 'StateletCallTree', order: Order, outcome: T,
            source_counts: Iterator, param_counts: Sequence
    ) -> 'tuple[StateletCallTree, CountletCallTree]':
        next_flats = []
        output_counts: MutableSequence = []
        for dungeonlets, statelets in zip(self.flats, statelet_tree.flats):
            next_statelets = []
            countlets: MutableSequence = []
            for dungeonlet, statelet in zip(dungeonlets, statelets):
                child_counts = [countlets[i] for i in dungeonlet.child_indexes]
                next_statelet, countlet = dungeonlet.next_state(
                    statelet, order, outcome, child_counts, source_counts,
                    param_counts)
                next_statelets.append(next_statelet)
                countlets.append(countlet)
            next_flats.append(tuple(next_statelets))
            output_counts.append(countlets[-1])
        next_statelet_calls = []
        countlet_calls = []
        for call_dungeonlet_tree, call_statelet_tree in zip(
                self.calls, statelet_tree.calls):
            next_call_statelet_tree, call_countlet_tree = call_dungeonlet_tree.next_state(
                call_statelet_tree, order, outcome, source_counts,
                output_counts)
            next_statelet_calls.append(next_call_statelet_tree)
            countlet_calls.append(call_countlet_tree)
        next_statelet_tree = StateletCallTree(tuple(next_flats),
                                              tuple(next_statelet_calls))
        countlet_tree = CountletCallTree(tuple(output_counts),
                                         tuple(countlet_calls))
        return next_statelet_tree, countlet_tree


class CountletCallTree(NamedTuple):
    flats: tuple
    calls: 'tuple[CountletCallTree, ...]'


class StateletCallTree(NamedTuple):
    flats: 'tuple[tuple[Hashable, ...], ...]'
    calls: 'tuple[StateletCallTree, ...]'


class QuestletCallTree(Generic[T], NamedTuple):
    flats: 'tuple[tuple[Questlet[T, Any], ...], ...]'
    calls: 'tuple[QuestletCallTree, ...]'

    def initial_state(
            self, order: Order, outcomes: tuple[T, ...],
            source_counts: Iterator, param_counts: Sequence
    ) -> 'tuple[StateletCallTree, CountletCallTree]':
        statelet_flats = []
        output_counts: MutableSequence = []
        for questlets in self.flats:
            statelets = []
            countlets: MutableSequence = []
            for questlet in questlets:
                child_counts = [countlets[i] for i in questlet.child_indexes]
                next_statelet, countlet = questlet.initial_state(
                    order, outcomes, child_counts, source_counts, param_counts)
                statelets.append(next_statelet)
                countlets.append(countlet)
            statelet_flats.append(tuple(statelets))
            output_counts.append(countlets[-1])
        statelet_calls = []
        countlet_calls = []
        for call_questlet_tree in self.calls:
            call_statelet_flats, call_countlet = call_questlet_tree.initial_state(
                order, outcomes, source_counts, countlets)
            statelet_calls.append(call_statelet_flats)
            countlet_calls.append(call_countlet)
        statelet_tree = StateletCallTree(tuple(statelet_flats),
                                         tuple(statelet_calls))
        countlet_tree = CountletCallTree(tuple(output_counts),
                                         tuple(countlet_calls))
        return statelet_tree, countlet_tree
