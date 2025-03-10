__docformat__ = 'google'

import operator
import icepool

from icepool.expression.multiset_expression_base import MultisetExpressionBase
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

    def has_parameters(self) -> bool:
        return False

    # Overridden to switch body generators with variables.

    @property
    def _body_inputs(self) -> 'tuple[MultisetTupleGenerator, ...]':
        return (self, )

    def _detach(
        self,
        body_inputs: 'list[MultisetExpressionBase]' = []
    ) -> 'MultisetTupleExpression':
        result = icepool.MultisetTupleVariable(False, len(body_inputs))
        body_inputs.append(self)
        return result

    def _apply_variables(self, outcome: T, body_counts: tuple[int, ...],
                         param_counts: tuple[int, ...]):
        raise icepool.MultisetVariableError(
            '_detach should have been called before _apply_variables.')
