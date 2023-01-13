import icepool.evaluator

from icepool.evaluator.multiset_evaluator import MultisetEvaluator
from icepool.expression.variable import MultisetVariable as MV

import inspect

from typing import Callable, TypeAlias, TypeVar, overload

NestedTupleOrEvaluator: TypeAlias = MultisetEvaluator | tuple[
    'NestedTupleOrEvaluator', ...]


def replace_tuples_with_joint_evaluator(
        tuple_or_evaluator: NestedTupleOrEvaluator, /) -> MultisetEvaluator:
    """Recursively replaces tuples with `JointEvaluator`s."""
    if isinstance(tuple_or_evaluator, tuple):
        return icepool.evaluator.JointEvaluator(*(
            replace_tuples_with_joint_evaluator(x) for x in tuple_or_evaluator))
    else:
        return tuple_or_evaluator


@overload
def evaluator_from_callable(func: Callable[[MV], NestedTupleOrEvaluator],
                            /) -> MultisetEvaluator:
    ...


@overload
def evaluator_from_callable(func: Callable[[MV, MV], NestedTupleOrEvaluator],
                            /) -> MultisetEvaluator:
    ...


@overload
def evaluator_from_callable(func: Callable[[MV, MV, MV],
                                           NestedTupleOrEvaluator],
                            /) -> MultisetEvaluator:
    ...


@overload
def evaluator_from_callable(func: Callable[[MV, MV, MV, MV],
                                           NestedTupleOrEvaluator],
                            /) -> MultisetEvaluator:
    ...


def evaluator_from_callable(func: Callable[..., NestedTupleOrEvaluator],
                            /) -> MultisetEvaluator:
    """EXPERIMENTAL: Creates an evaluator from a callable.

    The callable should take in multiset variables and output an evaluator,
    or a nested tuple of evaluators. For example, to compute the sums of each
    side's difference of two multisets:

    ```
    evaluator_from_callable(lambda a, b: ((a - b).sum(), (b - a).sum()))
    ```
    """
    parameters = inspect.signature(func).parameters
    for parameter in parameters.values():
        if parameter.kind not in [
                inspect.Parameter.POSITIONAL_ONLY or
                inspect.Parameter.POSITIONAL_OR_KEYWORD
        ] or parameter.default != inspect.Parameter.empty:
            raise ValueError(
                'Callable must take only a fixed number of positional arguments.'
            )
    tuple_or_evaluator = func(
        *icepool.expression.multiset_variables[:len(parameters)])
    return replace_tuples_with_joint_evaluator(tuple_or_evaluator)
