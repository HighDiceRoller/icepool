__docformat__ = 'google'

import icepool
from icepool.expression.multiset_expression_base import BodyDungeonlet, BodyQuestlet, Dungeonlet, Questlet, MultisetSourceBase
from icepool.expression.multiset_expression import MultisetExpression

import itertools
import math

from icepool.order import Order
from icepool.typing import T
from typing import Any, Callable, Hashable, Iterator, MutableSequence, Sequence

from abc import abstractmethod


class MultisetOperator(MultisetExpression[T]):
    """Internal node of an expression taking one or more `int` counts and producing a single `int` count."""
    _children: 'tuple[MultisetExpression[T], ...]'

    @abstractmethod
    def _next_state(self, state: Hashable, order: Order, outcome: T,
                    child_counts: Sequence, source_counts: Iterator,
                    arg_counts: Sequence) -> tuple[Hashable, int]:
        """Advances the state of the dungeonlet.
        
        Args:
            state: The local state.
            order: The order in which outcomes are seen by this method.
            outcome: The current outcome.
            child_counts: The counts of the child nodes.
            source_counts: The counts produced by freed sources.
                This is an iterator which will be progressively consumed by
                free variables.
            arg_counts: The counts produced by params.

        Returns:
            The next local state and the count produced by this node.

        Raises:
            UnsupportedOrder if the order is not supported.
        """

    @property
    @abstractmethod
    def _expression_key(self) -> Hashable:
        """Used to identify this expression node."""

    @property
    def _dungeonlet_key(self) -> Hashable:
        """Used to identify dungeonlets.

        This can exclude parts of _expression_key that don't affect next_state
        directly.
        
        Defaults to _expression_key.
        """
        return self._expression_key

    def _initial_state(self, order: Order, outcomes: Sequence[T],
                       child_sizes: Sequence, source_sizes: Iterator,
                       arg_sizes: Sequence) -> Hashable:
        """Optional: the initial state of this node.

        Args:
            order: The order in which `next_state` will see outcomes.
            outcomes: All outcomes that will be seen by `next_state` in ascending order.
            kwargs: Any keyword arguments that were passed to `evaluate()`.

        Returns:
            The initial state and the size of this node.

        Raises:
            UnsupportedOrder if the given order is not supported.
        """
        return None, None

    @property
    def hash_key(self):
        return self._expression_key, tuple(child.hash_key
                                           for child in self._children)

    @property
    def _static_keepable(self) -> bool:
        return False

    @property
    def _has_parameter(self) -> bool:
        return any(child._has_parameter for child in self._children)

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        for t in itertools.product(*(child._prepare()
                                     for child in self._children)):

            dungeonlets: MutableSequence[Dungeonlet[T, Any]] = []
            questlets: MutableSequence[Questlet[T, Any]] = []
            sources: MutableSequence[MultisetSourceBase[T, Any]] = []
            weight = 1
            positions: MutableSequence[int] = []
            for child_dungeonlets, child_questlets, child_sources, child_weight in t:
                dungeonlets.extend(child_dungeonlets)
                questlets.extend(child_questlets)
                sources.extend(child_sources)
                weight *= child_weight
                positions.append(len(dungeonlets))

            child_indexes = tuple(p - positions[-1] - 1 for p in positions)
            dungeonlet = BodyDungeonlet[T, int](self._next_state,
                                                self._dungeonlet_key,
                                                child_indexes)
            questlet = BodyQuestlet[T, int](self._initial_state, child_indexes)
            dungeonlets.append(dungeonlet)
            questlets.append(questlet)

            yield tuple(dungeonlets), tuple(questlets), tuple(sources), weight
