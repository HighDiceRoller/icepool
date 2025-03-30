__docformat__ = 'google'

import icepool
from icepool.expression.multiset_expression import MultisetExpression
from icepool.expression.multiset_expression_base import Dungeonlet, MultisetExpressionBase, Questlet, MultisetSourceBase
from icepool.operator.multiset_operator import MultisetOperatorDungeonlet, MultisetOperatorQuestlet
from icepool.order import Order

from icepool.typing import T
from typing import (Any, Hashable, Iterator, MutableSequence, Sequence)


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

    def _initial_state(self, order: Order, outcomes: Sequence[T],
                       child_sizes: MutableSequence, source_sizes: Iterator,
                       param_sizes: Sequence) -> Hashable:
        return None, child_sizes[self._index]

    def _next_state(self, state: Hashable, order: Order, outcome: T,
                    child_counts: MutableSequence, source_counts: Iterator,
                    param_counts: Sequence) -> tuple[Hashable, int]:
        return None, child_counts[0][self._index]

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        for dungeonlets, questlets, sources, weight in self._children[
                0]._prepare():
            child_indexes = (-1, )
            dungeonlet = MultisetOperatorDungeonlet[T](self._next_state,
                                                       self.hash_key,
                                                       child_indexes)
            questlet = MultisetOperatorQuestlet[T](self._initial_state,
                                                   child_indexes)

            yield dungeonlets + (dungeonlet, ), tuple(questlets) + (
                questlet, ), tuple(sources), weight
