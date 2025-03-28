__docformat__ = 'google'

import operator
import icepool

from icepool.evaluator.multiset_evaluator_base import MultisetDungeon, MultisetQuest
from icepool.expression.multiset_expression_base import MultisetDungeonlet, MultisetExpressionBase, MultisetFreeVariable, MultisetQuestlet, MultisetSourceBase
from icepool.expression.multiset_tuple_expression import MultisetTupleExpression
import icepool.generator
from icepool.generator.multiset_generator import MultisetSource
from icepool.typing import Outcome, Q, T, U_co

from abc import ABC, abstractmethod
from functools import cached_property

from typing import Any, Callable, Collection, Generic, Hashable, Iterator, Mapping, Sequence, TypeAlias, cast
"""The generator type returned by `_generate_min` and `_generate_max`.

Each element is a tuple of generator, counts, weight.
"""


class MultisetTupleGenerator(MultisetTupleExpression[T]):
    """Abstract base class for generating tuples of multisets."""

    _children = ()

    @abstractmethod
    def _make_source(self) -> 'MultisetTupleSource[T]':
        """Create a source from this generator."""

    @property
    def _has_param(self) -> bool:
        return False

    @property
    def _static_keepable(self) -> bool:
        return False

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[MultisetDungeonlet[T, Any], ...]',
                        'tuple[MultisetQuestlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        dungeonlets = (MultisetFreeVariable[T, tuple[int, ...]](), )
        questlets = (MultisetTupleGeneratorQuestlet[T](), )
        sources = (self._make_source(), )
        weight = 1
        yield dungeonlets, questlets, sources, weight


class MultisetTupleSource(MultisetSourceBase[T, tuple[int, ...]]):
    """A source that produces a tuple of `int` counts."""


class MultisetTupleGeneratorQuestlet(MultisetQuestlet[T, tuple[int, ...]]):
    child_indexes = ()

    def initial_state(self, order, outcomes, child_cardinalities,
                      source_cardinalities, param_cardinalities):
        return None, next(source_cardinalities)
