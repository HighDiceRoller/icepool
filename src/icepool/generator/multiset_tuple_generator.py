__docformat__ = 'google'

from icepool.expression.multiset_expression_base import Dungeonlet, MultisetFreeVariable, Questlet, MultisetSourceBase
from icepool.expression.multiset_tuple_expression import MultisetTupleExpression, IntTupleOut
from icepool.typing import T

from abc import abstractmethod

from typing import Any, Iterator
"""The generator type returned by `_generate_min` and `_generate_max`.

Each element is a tuple of generator, counts, weight.
"""


class MultisetTupleGenerator(MultisetTupleExpression[T, IntTupleOut]):
    """Abstract base class for generating tuples of multisets."""

    _children = ()

    @abstractmethod
    def _make_source(self) -> 'MultisetTupleSource[T, IntTupleOut]':
        """Create a source from this generator."""

    @property
    def _has_parameter(self) -> bool:
        return False

    @property
    def _static_keepable(self) -> bool:
        return False

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        dungeonlets = (MultisetFreeVariable[T, tuple[int, ...]](), )
        questlets = (MultisetTupleGeneratorQuestlet[T, IntTupleOut](), )
        sources = (self._make_source(), )
        weight = 1
        yield dungeonlets, questlets, sources, weight


class MultisetTupleSource(MultisetSourceBase[T, IntTupleOut]):
    """A source that produces a tuple of `int` counts."""


class MultisetTupleGeneratorQuestlet(Questlet[T, IntTupleOut]):
    child_indexes = ()

    def initial_state(self, order, outcomes, child_sizes, source_sizes,
                      arg_sizes):
        return None, next(source_sizes)
