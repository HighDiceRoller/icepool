__docformat__ = 'google'

import icepool
from icepool.expression.multiset_expression import MultisetExpression
from icepool.expression.multiset_expression_base import BodyDungeonlet, BodyQuestlet, Dungeonlet, MultisetExpressionBase, Questlet, MultisetSourceBase
from icepool.order import Order

from abc import abstractmethod
from icepool.typing import T
from typing import (TYPE_CHECKING, Any, Generic, Hashable, Iterator,
                    MutableSequence, Sequence, TypeVar, overload)

if TYPE_CHECKING:
    from icepool.expression.multiset_parameter import MultisetParameter, MultisetTupleParameter

IntTupleIn = TypeVar('IntTupleIn', bound=tuple[int, ...])
"""Count type for an input multiset tuple."""
IntTupleOut = TypeVar('IntTupleOut', bound=tuple[int, ...])
"""Count type for an output multiset tuple."""


class MultisetTupleExpression(MultisetExpressionBase[T, IntTupleOut]):
    """Abstract base class representing an expression that operates on tuples of multisets.
    
    Currently the only operations are to subscript or unpack to extract single
    multisets.
    """

    @abstractmethod
    def __len__(self) -> int:
        """The number of counts produced by this expression."""

    @overload
    def _make_param(
            self,
            name: str,
            arg_index: int,
            star_index: None = None
    ) -> 'MultisetTupleParameter[T, IntTupleOut]':
        ...

    @overload
    def _make_param(self, name: str, arg_index: int,
                    star_index: int) -> 'MultisetParameter[T]':
        ...

    @overload
    def _make_param(
        self,
        name: str,
        arg_index: int,
        star_index: int | None = None
    ) -> 'MultisetTupleParameter[T, IntTupleOut] | MultisetParameter[T]':
        ...

    def _make_param(
        self,
        name: str,
        arg_index: int,
        star_index: int | None = None
    ) -> 'MultisetTupleParameter[T, IntTupleOut] | MultisetParameter[T]':
        if star_index is None:
            return icepool.MultisetTupleParameter(name, arg_index, len(self))
        else:
            return icepool.MultisetParameter(name, arg_index, star_index)

    @overload
    def __getitem__(self, index: int,
                    /) -> 'MultisetTupleIndex[T, IntTupleOut]':
        ...

    @overload
    def __getitem__(self, index: slice,
                    /) -> 'MultisetTupleSlice[T, IntTupleOut, Any]':
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

    def __iter__(self) -> Iterator['MultisetTupleIndex[T, IntTupleOut]']:
        for i in range(len(self)):
            yield self[i]


class MultisetTupleIndex(Generic[T, IntTupleIn], MultisetExpression[T]):
    _children: 'tuple[MultisetTupleExpression[T, IntTupleIn]]'

    def __init__(self, child: MultisetTupleExpression[T, IntTupleIn], /, *,
                 index: int):
        self._index = index
        self._children = (child, )

    @property
    def _has_parameter(self):
        return self._children[0]._has_parameter

    @property
    def _static_keepable(self):
        return False

    @property
    def hash_key(self):
        return type(self), self._index

    def _initial_state(self, order: Order, outcomes: Sequence[T],
                       child_sizes: Sequence, source_sizes: Iterator,
                       arg_sizes: Sequence) -> Hashable:
        if child_sizes[0] is None:
            return None
        return None, child_sizes[0][self._index]

    def _next_state(self, state: Hashable, order: Order, outcome: T,
                    child_counts: Sequence, source_counts: Iterator,
                    arg_counts: Sequence) -> tuple[Hashable, int]:
        return None, child_counts[0][self._index]

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        for dungeonlets, questlets, sources, weight in self._children[
                0]._prepare():
            child_indexes = (-1, )
            dungeonlet = BodyDungeonlet[T, int](self._next_state,
                                                self.hash_key, child_indexes)
            questlet = BodyQuestlet[T, int](self._initial_state, child_indexes)

            yield dungeonlets + (dungeonlet, ), tuple(questlets) + (
                questlet, ), tuple(sources), weight


class MultisetTupleSlice(Generic[T, IntTupleIn, IntTupleOut],
                         MultisetTupleExpression[T, IntTupleIn]):
    _children: 'tuple[MultisetTupleExpression[T, IntTupleIn]]'

    def __init__(self, child: MultisetTupleExpression[T, IntTupleIn], /, *,
                 index: slice):
        self._index = index
        self._children = (child, )

    @property
    def _has_parameter(self):
        return self._children[0]._has_parameter

    @property
    def _static_keepable(self):
        return False

    @property
    def hash_key(self):
        return type(self), (self._index.start, self._index.step,
                            self._index.stop)

    def _initial_state(self, order: Order, outcomes: Sequence[T],
                       child_sizes: Sequence, source_sizes: Iterator,
                       arg_sizes: Sequence) -> Hashable:
        if child_sizes[0] is None:
            return None
        return None, child_sizes[0][self._index]

    def _next_state(self, state: Hashable, order: Order, outcome: T,
                    child_counts: Sequence, source_counts: Iterator,
                    arg_counts: Sequence) -> tuple[Hashable, int]:
        return None, child_counts[0][self._index]

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        for dungeonlets, questlets, sources, weight in self._children[
                0]._prepare():
            child_indexes = (-1, )
            dungeonlet = BodyDungeonlet[T, IntTupleOut](self._next_state,
                                                        self.hash_key,
                                                        child_indexes)
            questlet = BodyQuestlet[T, IntTupleOut](self._initial_state,
                                                    child_indexes)

            yield dungeonlets + (dungeonlet, ), tuple(questlets) + (
                questlet, ), tuple(sources), weight

    def __len__(self) -> int:
        test = [None] * len(self._children[0])
        return len(test[self._index])
