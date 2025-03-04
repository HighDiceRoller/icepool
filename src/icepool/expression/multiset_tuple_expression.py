__docformat__ = 'google'

from abc import abstractmethod
import icepool
from icepool.expression.multiset_expression import MultisetExpression
from icepool.expression.base import MultisetExpressionBase
from icepool.collection.counts import Counts
from icepool.order import Order, OrderReason, merge_order_preferences
from icepool.population.keep import highest_slice, lowest_slice

import bisect
import itertools
import operator
import random

from icepool.typing import Q, T, U, ImplicitConversionError, T
from types import EllipsisType
from typing import (Callable, Collection, Hashable, Iterator, Literal, Mapping,
                    Sequence, Type, cast, overload)


class MultisetTupleExpression(MultisetExpressionBase[T, tuple[int, ...]]):
    """Abstract base class representing an expression that operates on tuples of multisets.

    Currently the only operation is to subscript to produce a single multiset."""

    # Abstract overrides with more specific signatures.
    @abstractmethod
    def _generate_initial(
            self) -> Iterator[tuple['MultisetTupleExpression[T]', int]]:
        ...

    @abstractmethod
    def _generate_min(
        self, min_outcome: T
    ) -> Iterator[tuple['MultisetTupleExpression[T]', tuple[int, ...], int]]:
        ...

    @abstractmethod
    def _generate_max(
        self, max_outcome: T
    ) -> Iterator[tuple['MultisetTupleExpression[T]', tuple[int, ...], int]]:
        ...

    @abstractmethod
    def _detach(
        self,
        body_inputs: 'list[MultisetExpressionBase]' = []
    ) -> 'MultisetTupleExpression[T]':
        ...

    @abstractmethod
    def _apply_variables(
        self, outcome: T, body_counts: tuple[int,
                                             ...], param_counts: tuple[int,
                                                                       ...]
    ) -> 'tuple[MultisetTupleExpression[T], tuple[int, ...]]':
        ...

    @property
    def _variable_type(self) -> type:
        return icepool.MultisetTupleVariable

    def __getitem__(self, index: int, /) -> 'icepool.MultisetExpression[T]':
        return MultisetTupleSubscript(self, index=index)


class MultisetTupleSubscript(MultisetExpression[T]):
    _children: 'tuple[MultisetTupleExpression[T]]'

    def __init__(self, child: MultisetTupleExpression, /, *, index: int):
        self._index = index
        self._children = (child, )

    def outcomes(self) -> Sequence[T]:
        return self._children[0].outcomes()

    def _is_resolvable(self) -> bool:
        return self._children[0]._is_resolvable()

    def _generate_initial(self):
        for child, weight in self._children[0]._generate_initial():
            yield MultisetTupleSubscript(child, index=self._index), weight

    def _generate_min(
        self, min_outcome: T
    ) -> Iterator[tuple['MultisetTupleSubscript[T]', int, int]]:
        for child, counts, weight in self._children[0]._generate_min(
                min_outcome):
            yield MultisetTupleSubscript(
                child, index=self._index), counts[self._index], weight

    def _generate_max(
        self, min_outcome: T
    ) -> Iterator[tuple['MultisetTupleSubscript[T]', int, int]]:
        for child, counts, weight in self._children[0]._generate_max(
                min_outcome):
            yield MultisetTupleSubscript(
                child, index=self._index), counts[self._index], weight

    def has_parameters(self) -> bool:
        return self._children[0].has_parameters()

    def _detach(self, body_inputs: 'list[MultisetExpressionBase]' = []):
        if self.has_parameters():
            child = self._children[0]._detach(body_inputs)
            return MultisetTupleSubscript(child, index=self._index)
        else:
            result = icepool.MultisetVariable(False, len(body_inputs))
            body_inputs.append(self)
            return result

    def _apply_variables(self, outcome: T, body_counts: tuple[int, ...],
                         param_counts: tuple[int, ...]):
        child, counts = self._children[0]._apply_variables(
            outcome, body_counts, param_counts)
        return MultisetTupleSubscript(child,
                                      index=self._index), counts[self._index]

    def local_order_preference(self):
        return self._children[0].local_order_preference()

    @property
    def _local_hash_key(self) -> Hashable:
        return type(self)
