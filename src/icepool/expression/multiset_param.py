__docformat__ = 'google'

from icepool.expression.multiset_expression_base import Dungeonlet, MultisetExpressionBase, Questlet, MultisetSourceBase
from icepool.expression.multiset_tuple_expression import MultisetTupleExpression
from icepool.order import Order
from icepool.expression.multiset_expression import MultisetExpression

import enum

from typing import Any, Generic, Hashable, Iterator, MutableSequence, Sequence

from icepool.typing import Q, T, U_co


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

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        dungeonlet = MultisetParamDungeonlet[T](self._index)
        questlet = MultisetParamQuestlet[T](self._index)
        yield (dungeonlet, ), (questlet, ), (), 1

    @property
    def _has_param(self):
        return True

    @property
    def _static_keepable(self):
        return False

    def hash_key(self):
        return type(self), self._index


class MultisetParam(MultisetParamBase[T], MultisetExpression[T]):
    """A multiset param with a count of a single `int`."""


class MultisetTupleParam(MultisetParamBase[T], MultisetTupleExpression[T]):
    """A multiset param with a count of a tuple of `int`s."""


class MultisetParamDungeonlet(Dungeonlet[T, Any]):
    child_indexes = ()

    def __init__(self, index: int):
        self.index = index

    def next_state(self, state, order, outcome, child_counts, source_counts,
                   param_counts):
        return None, param_counts[self.index]

    @property
    def hash_key(self):
        return MultisetParamDungeonlet, self.index


class MultisetParamQuestlet(Questlet[T, Any]):
    child_indexes = ()

    def __init__(self, index: int):
        self.index = index

    def initial_state(self, order: Order, outcomes: Sequence[T],
                      child_sizes: MutableSequence, source_sizes: Iterator,
                      param_sizes: Sequence):
        return None, param_sizes[self.index]
