__docformat__ = 'google'

import icepool
from icepool.expression.multiset_expression_base import MultisetExpressionBase, MultisetDungeonlet, MultisetQuestlet
from icepool.expression.multiset_expression import MultisetExpression, MultisetExpressionDungeonlet

import itertools
import math

from icepool.order import Order
from icepool.typing import T, Q
from typing import Callable, Collection, Hashable, Iterator, MutableSequence, Sequence

from abc import abstractmethod


class MultisetOperator(MultisetExpression[T]):
    """Internal node of an expression taking one or more `int` counts and producing a single `int` count."""
    _children: 'tuple[MultisetExpression[T], ...]'

    @abstractmethod
    def _next_state(self, state: Hashable, order: Order, outcome: T,
                    child_counts: MutableSequence, free_counts: Iterator,
                    param_counts: Sequence) -> tuple[Hashable, int]:
        """Advances the state of the dungeonlet.
        
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
    def _dungeonlet_key(self) -> Hashable:
        """Used to identify dungeonlets. Only has to cover this node and does not need to include child_indexes."""

    def _initial_state(self, order: Order, outcomes: Sequence[T], /,
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

    def _prepare(self):
        for t in itertools.product(*(child._prepare()
                                     for child in self._children)):

            dungeonlets = []
            questlets = []
            free_sources = []
            weight = 1
            positions = []
            for child_dungeonlets, child_questlets, child_free_sources, child_weight in t:
                dungeonlets.extend(child_dungeonlets)
                questlets.extend(child_questlets)
                free_sources.extend(child_free_sources)
                weight *= child_weight
                positions.append(len(dungeonlets))

            child_indexes = tuple(p - positions[-1] - 1 for p in positions)
            dungeonlet = MultisetOperatorDungeonlet(self._next_state,
                                                    self._dungeonlet_key,
                                                    child_indexes)
            questlet = MultisetOperatorQuestlet(self._extra_outcomes,
                                                self._initial_state)
            dungeonlets.append(dungeonlet)
            questlets.append(questlet)

            yield dungeonlets, questlets, free_sources, weight


class MultisetOperatorDungeonlet(MultisetExpressionDungeonlet[T]):
    # Will be filled in by the constructor.
    next_state = None  # type: ignore

    def __init__(self, next_state: Callable, hash_key: Hashable,
                 child_indexes: tuple[int, ...]):
        self.next_state = next_state  # type: ignore
        self.hash_key = (hash_key, child_indexes)  # type: ignore
        self.child_indexes = child_indexes


class MultisetOperatorQuestlet(MultisetQuestlet[T]):
    # Will be filled in by the constructor.
    initial_state = None  # type: ignore

    def __init__(self, extra_outcomes: Callable, initial_state: Callable):
        self.initial_state = initial_state  # type: ignore
