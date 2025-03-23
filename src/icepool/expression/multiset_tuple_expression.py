__docformat__ = 'google'

from abc import abstractmethod
import icepool
from icepool.expression.multiset_expression import MultisetExpression
from icepool.expression.multiset_expression_base import MultisetExpressionBase, MultisetExpressionPreparation
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

    @property
    def _param_type(self):
        return icepool.MultisetTupleParam

    def __getitem__(self, index: int, /) -> 'icepool.MultisetExpression[T]':
        return MultisetTupleSubscript(self, index=index)


class MultisetTupleSubscript(MultisetExpression[T]):
    _children: 'tuple[MultisetTupleExpression[T]]'

    _can_keep = False

    def __init__(self, child: MultisetTupleExpression, /, *, index: int):
        self._index = index
        self._children = (child, )
