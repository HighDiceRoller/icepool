__docformat__ = 'google'

import icepool

from icepool.typing import Evaluable, Outcome

from typing import Callable, Generic, Mapping, Sequence, Type, TypeAlias, TypeVar
import warnings

T = TypeVar('T', bound=Outcome)
"""Type variable representing the outcome type."""

T_co = TypeVar('T_co', bound=Outcome, covariant=True)
"""Type variable representing the outcome type."""


class GeneratorsWithExpression(Generic[T_co]):
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

    # Binary operators.

    def __add__(self: Evaluable,
                other: Evaluable) -> 'GeneratorsWithExpression[T_co]':
        try:
            return binary_operation(self, other,
                                    icepool.expression.DisjointUnionExpression)
        except TypeError:
            return NotImplemented

    def __radd__(self: Evaluable,
                 other: Evaluable) -> 'GeneratorsWithExpression[T_co]':
        try:
            return binary_operation(other, self,
                                    icepool.expression.DisjointUnionExpression)
        except TypeError:
            return NotImplemented

    # Count adjustment.

    def unique(self: Evaluable,
               max_count: int = 1) -> 'GeneratorsWithExpression[T_co]':
        """Counts each outcome at most `max_count` times.

        For example, `generator.unique(2)` would count each outcome at most
        twice.
        """
        return adjust_counts(self, max_count,
                             icepool.expression.UniqueExpression)

    # Evaluators.


def convert(
    arg: 'Evaluable[T]',
) -> tuple[list['icepool.MultisetGenerator[T, tuple[int]]'],
           'icepool.expression.MultisetExpression']:
    """Converts a single argument to a list of generators and an expression."""
    if isinstance(arg, GeneratorsWithExpression):
        return list(arg.generators), arg.expression
    elif isinstance(arg, (icepool.MultisetGenerator, Mapping, Sequence)):
        return [icepool.implicit_convert_to_generator(arg)
               ], icepool.expression.MultisetVariable(0)
    else:
        raise TypeError(f'Could not convert argument of type {type(arg)}.')


def merge(
    *args: 'Evaluable[T]',
) -> tuple[list['icepool.MultisetGenerator[T, tuple[int]]'],
           list['icepool.expression.MultisetExpression']]:
    """Merges a number of GeneratorsWithExpression together, returning a sequence of generators and a sequence of expressions.

    Args:
        *args: These may be one of the following:
            * `GeneratorsWithExpression`
            * `MultisetGenerator`, which is treated as a single generator
                with the identity expression `MultisetVariable(0)`.
            * `Mapping` or `Sequence`, which is treated as a generator
                that always outputs that multiset.

    Raises:
        `TypeError` if the arguments are not of valid type.
    """
    generators: list['icepool.MultisetGenerator[T, tuple[int]]'] = []
    expressions: list[icepool.expression.MultisetExpression] = []
    for arg in args:
        arg_generators, arg_expression = convert(arg)
        expressions += [arg_expression.shift_variables(len(generators))]
        generators += arg_generators

    return generators, expressions


def binary_operation(
    left: 'Evaluable[T]', right: 'Evaluable[T]',
    operation_class: 'Type[icepool.expression.BinaryOperatorExpression]'
) -> 'GeneratorsWithExpression[T]':
    generators: list['icepool.MultisetGenerator[T, tuple[int]]']
    generators, expressions = merge(left, right)
    expression = operation_class(*expressions)
    return GeneratorsWithExpression(*generators, expression=expression)


def adjust_counts(
    left: 'Evaluable[T]', constant: int,
    operation_class: 'Type[icepool.expression.AdjustCountsExpression]'
) -> 'GeneratorsWithExpression[T]':
    generators: list['icepool.MultisetGenerator[T, tuple[int]]']
    generators, expressions = merge(left)
    expression = operation_class(expressions[0], constant)
    return GeneratorsWithExpression(generators[0], expression=expression)


def compare(
    left: 'Evaluable[T]', right: 'Evaluable[T]',
    cls: Type['icepool.evaluator.ComparisonEvaluator[T]']
) -> 'icepool.Die[bool]':
    if isinstance(right, (Mapping, Sequence)):
        # Right-hand side is a constant.
        evaluator = cls(right)
        return evaluator.evaluate(left)
    else:
        # Right-hand side is an expression.
        evaluator = cls()
        return evaluator.evaluate(left, right)
