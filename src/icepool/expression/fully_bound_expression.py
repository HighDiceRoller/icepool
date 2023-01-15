__docformat__ = 'google'

import icepool

from icepool.evaluable_interface import EvaluableInterface

import functools
import operator

from typing import Callable, Generic, Mapping, Sequence, Type, TypeAlias, TypeVar

from icepool.typing import Evaluable, Outcome

T = TypeVar('T', bound=Outcome)
"""An outcome type."""

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""An outcome type."""

U = TypeVar('U', bound=Outcome)
"""Another outcome type."""


class FullyBoundExpression(EvaluableInterface[T_co]):
    """An expression without any free variables.

    This is used to implement method chaining on generators.
    It is not intended to be instantiated directly.
    """

    def __init__(self,
                 expression: 'icepool.expression.MultisetExpression') -> None:
        self._expression = expression

    @property
    def expression(self) -> 'icepool.expression.MultisetExpression':
        return self._expression
