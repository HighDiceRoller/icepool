__docformat__ = 'google'

import icepool
from icepool.expression.base import MultisetExpressionBase
from icepool.collection.counts import Counts
from icepool.order import Order, OrderReason, merge_order_preferences
from icepool.population.keep import highest_slice, lowest_slice

import bisect
import itertools
import operator
import random

from icepool.typing import Q, T, U, Expandable, ImplicitConversionError, T
from types import EllipsisType
from typing import (Callable, Collection, Literal, Mapping, Sequence, Type,
                    cast, overload)


class MultisetTupleExpression(MultisetExpressionBase[T, tuple[int, ...]],
                              Expandable[tuple[T, ...]]):
    """Abstract base class representing an expression that operates on tuples of multisets.

    Currently the only operation is to subscript to produce a single multiset."""
