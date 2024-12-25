__docformat__ = 'google'

import operator
import icepool

import icepool.generator
from icepool.collection.counts import Counts
from icepool.multiset_expression import MultisetExpression
from icepool.generator.pop_order import PopOrderReason
from icepool.typing import Order, Outcome, Qs, T

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


class MultisetGenerator(Generic[T, Qs], MultisetExpression[T]):
    """Abstract base class for generating one or more multisets.

    These include dice pools (`Pool`) and card deals (`Deal`). Most likely you
    will be using one of these two rather than writing your own subclass of
    `MultisetGenerator`.

    The multisets are incrementally generated one outcome at a time.
    For each outcome, a `count` and `weight` are generated, along with a
    smaller generator to produce the rest of the multiset.

    You can perform simple evaluations using built-in operators and methods in
    this class.
    For more complex evaluations and better performance, particularly when
    multiple generators are involved, you will want to write your own subclass
    of `MultisetEvaluator`.
    """

    _children = ()

    @property
    def _can_keep(self) -> bool:
        """Whether the generator supports enhanced keep operations."""
        return False

    def _free_arity(self) -> int:
        return 0

    def order(self) -> Order:
        return Order.Any

    # Overridden to switch bound generators with variables.

    @property
    def _bound_generators(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return (self, )

    def _unbind(self, next_index: int) -> 'tuple[MultisetExpression, int]':
        unbound_expression = icepool.MultisetVariable(index=next_index)
        return unbound_expression, next_index + 1
