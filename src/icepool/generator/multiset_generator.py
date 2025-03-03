__docformat__ = 'google'

import operator
import icepool

from icepool.expression.base import MultisetExpressionBase
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

    def has_parameters(self) -> bool:
        return False

    # Overridden to switch body generators with variables.

    @property
    def _body_inputs(self) -> 'tuple[icepool.MultisetGenerator, ...]':
        return (self, )

    def _detach(self, body_inputs: 'list[MultisetExpressionBase]' = []):
        result = icepool.MultisetVariable(False, len(body_inputs))
        body_inputs.append(self)
        return result

    def _apply_variables(self, outcome: T, body_counts: tuple[int, ...],
                         param_counts: tuple[int, ...]):
        raise icepool.MultisetVariableError(
            '_detach should have been called before _apply_variables.')
