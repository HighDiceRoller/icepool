__docformat__ = 'google'

import icepool
from icepool.expression.multiset_expression import MultisetExpression
from icepool.expression.multiset_expression_base import Dungeonlet, MultisetExpressionBase, Questlet, MultisetSourceBase
from icepool.operator.multiset_operator import MultisetOperatorDungeonlet, MultisetOperatorQuestlet
from icepool.order import Order

from abc import abstractmethod
from icepool.typing import T
from typing import (TYPE_CHECKING, Any, Hashable, Iterator, MutableSequence,
                    Sequence, overload)

if TYPE_CHECKING:
    from icepool.expression.multiset_param import MultisetParamBase


class MultisetTupleExpression(MultisetExpressionBase[T, tuple[int, ...]]):
    """Abstract base class representing an expression that operates on tuples of multisets.
    
    Currently the only operations are to subscript or unpack to extract single
    multisets.
    """

    @abstractmethod
    def __len__(self) -> int:
        """The number of counts produced by this expression."""

    def _make_param(self, index: int, name: str) -> 'MultisetParamBase[T]':
        return icepool.MultisetTupleParam(index, name, len(self))

    @overload
    def __getitem__(self, index: int, /) -> 'MultisetTupleIndex[T]':
        ...

    @overload
    def __getitem__(self, index: slice, /) -> 'MultisetTupleSlice[T]':
        ...

    @overload
    def __getitem__(self, index: int | slice,
                    /) -> 'MultisetExpressionBase[T, Any]':
        ...

    def __getitem__(self, index: int | slice,
                    /) -> 'MultisetExpressionBase[T, Any]':
        if isinstance(index, int):
            return MultisetTupleIndex(self, index=index)
        elif isinstance(index, slice):
            return MultisetTupleSlice(self, index=index)

    def __iter__(self) -> Iterator['MultisetTupleIndex[T]']:
        for i in range(len(self)):
            yield self[i]


class MultisetTupleIndex(MultisetExpression[T]):
    _children: 'tuple[MultisetTupleExpression[T]]'

    def __init__(self, child: MultisetTupleExpression[T], /, *, index: int):
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
        return type(self), self._index

    def _initial_state(self, order: Order, outcomes: Sequence[T],
                       child_sizes: MutableSequence, source_sizes: Iterator,
                       param_sizes: Sequence) -> Hashable:
        if child_sizes[0] is None:
            return None
        return None, child_sizes[0][self._index]

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


class MultisetTupleSlice(MultisetTupleExpression[T]):
    _children: 'tuple[MultisetTupleExpression[T]]'

    def __init__(self, child: MultisetTupleExpression[T], /, *, index: slice):
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
        return type(self), (self._index.start, self._index.step,
                            self._index.stop)

    def _initial_state(self, order: Order, outcomes: Sequence[T],
                       child_sizes: MutableSequence, source_sizes: Iterator,
                       param_sizes: Sequence) -> Hashable:
        if child_sizes[0] is None:
            return None
        return None, child_sizes[0][self._index]

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
            # TODO: adjust these types
            dungeonlet = MultisetOperatorDungeonlet[T](self._next_state,
                                                       self.hash_key,
                                                       child_indexes)
            questlet = MultisetOperatorQuestlet[T](self._initial_state,
                                                   child_indexes)

            yield dungeonlets + (dungeonlet, ), tuple(questlets) + (
                questlet, ), tuple(sources), weight

    def __len__(self) -> int:
        test = [None] * len(self._children[0])
        return len(test[self._index])
