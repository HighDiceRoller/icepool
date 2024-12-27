__docformat__ = 'google'

import operator
import icepool

import icepool.generator
from icepool.collection.counts import Counts
from icepool.multiset_expression import MultisetExpression
from icepool.order import Order, OrderReason
from icepool.typing import Outcome, Qs, T

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

    def has_free_variables(self) -> bool:
        return False

    # Overridden to switch bound generators with variables.

    @property
    def _bound_inputs(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return (self, )

    def _unbind(
            self,
            bound_inputs: 'list[MultisetExpression]' = []
    ) -> 'MultisetExpression':
        result = icepool.MultisetVariable(False, len(bound_inputs))
        bound_inputs.append(self)
        return result

    def _apply_variables(
            self, outcome: T, bound_counts: tuple[int, ...],
            free_counts: tuple[int, ...]) -> 'MultisetExpression[T]':
        raise icepool.MultisetBindingError(
            '_unbind should have been called before _apply_variables.')
