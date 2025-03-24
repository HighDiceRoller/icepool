__docformat__ = 'google'

import operator
import icepool

from icepool.evaluator.multiset_evaluator_base import MultisetDungeon, MultisetQuest
from icepool.expression.multiset_expression_base import MultisetDungeonlet, MultisetExpressionBase, MultisetFreeVariable, MultisetQuestlet, MultisetSourceBase
import icepool.generator
from icepool.collection.counts import Counts
from icepool.expression.multiset_expression import MultisetExpression
from icepool.order import Order, OrderReason
from icepool.typing import Outcome, Q, T, U_co

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


class MultisetGenerator(MultisetExpression[T]):
    """Abstract base class for generating multisets.

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

    @abstractmethod
    def _make_source(self) -> 'MultisetSource':
        """Create a source from this generator."""

    @property
    def _has_param(self) -> bool:
        return False

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[MultisetDungeonlet[T, Any], ...]',
                        'Sequence[MultisetQuestlet[T]]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        dungeonlets = (MultisetFreeVariable[T, int](), )
        questlets = (MultisetQuestlet[T](), )
        sources = (self._make_source(), )
        weight = 1
        yield dungeonlets, questlets, sources, weight


class MultisetSource(MultisetSourceBase[T, int]):
    """A source that produces a single `int` count."""
