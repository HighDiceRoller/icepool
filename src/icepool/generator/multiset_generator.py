__docformat__ = 'google'

import icepool
from icepool.expression.multiset_expression_base import Dungeonlet, MultisetFreeVariable, Questlet, MultisetSourceBase
from icepool.expression.multiset_expression import MultisetExpression
from icepool.typing import T

from abc import abstractmethod

from typing import Any, Iterator
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
    def _has_parameter(self) -> bool:
        return False

    def _prepare(
        self
    ) -> Iterator[tuple['tuple[Dungeonlet[T, Any], ...]',
                        'tuple[Questlet[T, Any], ...]',
                        'tuple[MultisetSourceBase[T, Any], ...]', int]]:
        dungeonlets = (MultisetFreeVariable[T, int](), )
        questlets = (MultisetGeneratorQuestlet[T](), )
        sources = (self._make_source(), )
        weight = 1
        yield dungeonlets, questlets, sources, weight

    def weightless(self) -> 'MultisetGenerator[T]':
        """EXPERIMENTAL: Produces a wrapped generator in which each possible multiset is equally weighted.

        In other words, given a generator `g`,
        ```python
        g.expand()
        g.weightless().expand()
        ```
        have the same set of outcomes, but the weightless version has every
        outcome with quantity 1. Other operators and evaluations can be
        attached to the result of `weightless()` as usual, in which case the
        quantity of each outcome the number of *unique* multisets producing that
        given outcome, rather than the ordinary probabilistic weighting.
        
        `weightless()` requires that each call to the underlying `source.pop()`  
        does not yield duplicate count values; if so, the evaluation will raise
        `UnsupportedOrder`. Keeps and mixed pools usually fail this.
        """
        if isinstance(self, icepool.WeightlessGenerator):
            return self
        return icepool.WeightlessGenerator(self)


class MultisetSource(MultisetSourceBase[T, int]):
    """A source that produces a single `int` count."""


class MultisetGeneratorQuestlet(Questlet[T, int]):
    child_indexes = ()

    def initial_state(self, order, outcomes, child_sizes, source_sizes,
                      arg_sizes):
        return None, next(source_sizes)
