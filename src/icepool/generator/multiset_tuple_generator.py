__docformat__ = 'google'

import operator
import icepool

from icepool.expression.base import MultisetExpressionBase
from icepool.expression.multiset_tuple_expression import MultisetTupleExpression
import icepool.generator
from icepool.collection.counts import Counts
from icepool.expression.multiset_expression import MultisetExpression
from icepool.order import Order, OrderReason
from icepool.typing import Outcome, Q, T

import bisect
import functools
import itertools
import random

from abc import ABC, abstractmethod
from functools import cached_property

from typing import Any, Callable, Collection, Generic, Hashable, Iterator, Mapping, Sequence, TypeAlias, cast
"""The generator type returned by `_generate_min` and `_generate_max`.

Each element is a tuple of generator, counts, weight.
"""


class MultisetTupleGenerator(MultisetTupleExpression[T]):
    """Abstract base class for generating tuples of multisets."""

    _children = ()

    def has_free_variables(self) -> bool:
        return False

    # Overridden to switch bound generators with variables.

    @property
    def _bound_inputs(self) -> 'tuple[MultisetTupleGenerator, ...]':
        return (self, )

    def _unbind(
        self,
        bound_inputs: 'list[MultisetExpressionBase]' = []
    ) -> 'MultisetExpressionBase':
        result = icepool.MultisetVariable(False, len(bound_inputs))
        bound_inputs.append(self)
        return result

    def _apply_variables(self, outcome: T, bound_counts: tuple[int, ...],
                         free_counts: tuple[int, ...]):
        raise icepool.MultisetBindingError(
            '_unbind should have been called before _apply_variables.')
