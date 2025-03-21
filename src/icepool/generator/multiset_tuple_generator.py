__docformat__ = 'google'

import operator
import icepool

from icepool.expression.multiset_expression_base import MultisetExpressionBase, MultisetFreeVariable, MultisetQuestlet, MultisetSourceBase
from icepool.expression.multiset_tuple_expression import MultisetTupleExpression
import icepool.generator
from icepool.typing import Outcome, Q, T

from abc import ABC, abstractmethod
from functools import cached_property

from typing import Any, Callable, Collection, Generic, Hashable, Iterator, Mapping, Sequence, TypeAlias, cast
"""The generator type returned by `_generate_min` and `_generate_max`.

Each element is a tuple of generator, counts, weight.
"""


class MultisetTupleGenerator(MultisetTupleExpression[T]):
    """Abstract base class for generating tuples of multisets."""

    _children = ()

    def _prepare(self):
        dungeonlets = [MultisetFreeVariable()]
        broods = [()]
        questlets = [MultisetQuestlet()]
        sources = [self]  # inherit from MultisetSource?
        weight = 1
        return dungeonlets, broods, questlets, sources, weight
