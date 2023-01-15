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


class GeneratorsWithExpression(EvaluableInterface[T_co]):
    """One or more generators feeding into a single expression."""

    def __init__(self,
                 *generators: 'icepool.MultisetGenerator[T_co, tuple[int]]',
                 expression: 'icepool.expression.MultisetExpression') -> None:
        if any(generator.arity != 1 for generator in generators):
            raise ValueError(
                'Direct evaluation is only valid for MultisetGenerators with exactly one output.'
            )
        self._generators = generators
        self._expression = expression

    @property
    def generators(
            self) -> 'tuple[icepool.MultisetGenerator[T_co, tuple[int]], ...]':
        return self._generators

    @property
    def expression(self) -> 'icepool.expression.MultisetExpression':
        return self._expression
