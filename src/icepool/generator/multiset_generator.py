__docformat__ = 'google'

import operator
import icepool

from icepool.expression.multiset_expression_base import MultisetExpressionBase, MultisetFreeVariable, MultisetQuestlet, MultisetSource
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

    def _prepare(self):
        dungeonlets = [MultisetFreeVariable()]
        broods = [()]
        questlets = [MultisetQuestlet()]
        sources = [self]  # inherit from MultisetSource?
        weight = 1
        return dungeonlets, broods, questlets, sources, weight
