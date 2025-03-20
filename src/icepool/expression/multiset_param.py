__docformat__ = 'google'

import icepool
from icepool.expression.multiset_expression_base import MultisetDungeonlet, MultisetExpressionBase, MultisetQuestlet
from icepool.expression.multiset_tuple_expression import MultisetTupleExpression
from icepool.order import Order, OrderReason
from icepool.expression.multiset_expression import MultisetExpression

import enum

from typing import Any, Generic, Hashable, Iterator, MutableSequence, Sequence

from icepool.typing import Q, T


class MultisetParamBase(Generic[T]):
    _children: 'tuple[MultisetExpressionBase[T, Any], ...]' = ()

    def __init__(self, index: int, name: str | None = None):
        self._index = index
        if name is None:
            self._name = f'mv[{index}]'
        else:
            self._name = name

    def __str__(self) -> str:
        return self._name

    def _prepare(self):
        dungeonlet = MultisetParamDungeonlet(self._index)
        questlet = MultisetParamQuestlet()
        yield [dungeonlet], [questlet], [], 1


class MultisetParam(MultisetExpression[T], MultisetParamBase[T]):
    """A multiset param with a count of a single `int`."""


class MultisetTupleParam(MultisetTupleExpression[T], MultisetParamBase[T]):
    """A multiset param with a count of a tuple of `int`s."""


class MultisetParamDungeonlet(MultisetDungeonlet[T, Any]):

    def __init__(self, index: int):
        self.index = index

    def next_state(self, state, order, outcome, child_counts, free_counts,
                   param_counts):
        return None, param_counts[self.index]

    @property
    def hash_key(self):
        return (type(self), self.index)


class MultisetParamQuestlet(MultisetQuestlet[T]):
    pass
