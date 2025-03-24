__docformat__ = 'google'

from abc import abstractmethod
import icepool
from icepool.expression.multiset_expression import MultisetExpression, MultisetExpressionDungeonlet
from icepool.expression.multiset_expression_base import MultisetDungeonlet, MultisetExpressionBase, MultisetQuestlet, MultisetSourceBase
from icepool.collection.counts import Counts
from icepool.operator.multiset_operator import MultisetOperatorDungeonlet, MultisetOperatorQuestlet
from icepool.order import Order, OrderReason, merge_order_preferences
from icepool.population.keep import highest_slice, lowest_slice

import bisect
import itertools
import operator
import random

from icepool.typing import Q, T, U, ImplicitConversionError, T
from types import EllipsisType
from typing import (Any, Callable, Collection, Hashable, Iterator, Literal,
                    Mapping, MutableSequence, Sequence, Type, cast, overload)


class MultisetTupleExpression(MultisetExpressionBase[T, tuple[int, ...]]):
    """Abstract base class representing an expression that operates on tuples of multisets.

    Currently the only operation is to subscript to produce a single multiset."""

    @property
    def _param_type(self):
        return icepool.MultisetTupleParam

    def __getitem__(self, index: int, /) -> 'icepool.MultisetExpression[T]':
        return MultisetTupleSubscript(self, index=index)


class MultisetTupleSubscript(MultisetExpression[T]):
    _children: 'tuple[MultisetTupleExpression[T]]'

    def __init__(self, child: MultisetTupleExpression, /, *, index: int):
        self._index = index
        self._children = (child, )

    @property
    def _has_param(self):
        return self._children[0]._has_param

    @property
    def _static_keepable(self):
        return False

    @property
    def hash_key(self):
        return MultisetTupleSubscript, self._index

    def _initial_state(self, order: Order, outcomes: Sequence[T]) -> Hashable:
        return None

    def _next_state(self, state: Hashable, order: Order, outcome: T,
                    child_counts: MutableSequence, source_counts: Iterator,
                    param_counts: Sequence) -> tuple[Hashable, int]:
        return None, child_counts[0][self._index]

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[MultisetDungeonlet[T, Any], ...]',
                        'tuple[MultisetQuestlet[T], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        for dungeonlets, questlets, sources, weight in self._children[
                0]._prepare():
            child_indexes = (-1, )
            dungeonlet = MultisetOperatorDungeonlet[T](self._next_state,
                                                       self.hash_key,
                                                       child_indexes)
            questlet = MultisetOperatorQuestlet[T](self._initial_state)

            yield dungeonlets + (dungeonlet, ), tuple(questlets) + (
                questlet, ), tuple(sources), weight
